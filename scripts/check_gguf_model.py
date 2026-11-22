from __future__ import annotations

import argparse
from pathlib import Path
import sys
from typing import Any


EXPECTED_ARCHITECTURE = "granite"
EXPECTED_FILE_TYPE = 15
MIN_MODEL_BYTES = 1_500_000_000
REQUIRED_TEMPLATE_MARKERS = ("{{", "messages", "assistant")
REQUIRED_LAYER_TENSORS = (
    "attn_q.weight",
    "attn_k.weight",
    "attn_v.weight",
    "attn_output.weight",
    "attn_norm.weight",
    "ffn_gate.weight",
    "ffn_up.weight",
    "ffn_down.weight",
    "ffn_norm.weight",
)


def _field_value(reader: Any, key: str) -> Any:
    field = reader.fields.get(key)
    if field is None:
        raise ValueError(f"GGUF is missing required metadata field {key!r}.")
    return field.contents()


def validate_architecture_tensors(
    architecture: str,
    tensor_names: list[str],
    head_count_kv: Any,
    expected_layer_count: int,
) -> None:
    has_ssm_tensors = any(".ssm_" in name or ".ssm." in name for name in tensor_names)
    if architecture == "granitehybrid" and not has_ssm_tensors:
        if (
            isinstance(head_count_kv, (list, tuple))
            and head_count_kv
            and all(int(head_count) == 0 for head_count in head_count_kv)
        ):
            raise ValueError(
                "Incompatible Granite-Hybrid GGUF: metadata marks all "
                f"{len(head_count_kv)} layers as recurrent (attention.head_count_kv=0), "
                "but the file contains no SSM tensors. llama.cpp will request "
                "'blk.0.ssm_in.weight' and fail. The merged checkpoint describes "
                "full-attention layers; this GGUF must be rebuilt from that checkpoint."
            )
        raise ValueError(
            "The merged checkpoint is full-attention, but this Granite-Hybrid GGUF "
            "does not contain the expected SSM weights."
        )
    if architecture != EXPECTED_ARCHITECTURE:
        raise ValueError(
            f"Expected dense Granite architecture {EXPECTED_ARCHITECTURE!r}, "
            f"found {architecture!r}."
        )
    if (
        not isinstance(head_count_kv, (list, tuple))
        or len(head_count_kv) != expected_layer_count
        or any(int(head_count) <= 0 for head_count in head_count_kv)
    ):
        raise ValueError(
            "Dense Granite metadata must contain a positive KV-head count for "
            f"each of its {expected_layer_count} attention layers."
        )

    tensor_name_set = set(tensor_names)
    missing_tensors = [
        f"blk.{layer}.{suffix}"
        for layer in range(expected_layer_count)
        for suffix in REQUIRED_LAYER_TENSORS
        if f"blk.{layer}.{suffix}" not in tensor_name_set
    ]
    if missing_tensors:
        raise ValueError(
            "Dense Granite GGUF is missing required full-attention/FFN tensors: "
            f"{missing_tensors[:8]}."
        )


def inspect_gguf(
    model_path: Path,
    gguf_python_path: Path,
    expected_file_type: int = EXPECTED_FILE_TYPE,
) -> dict[str, Any]:
    if not model_path.is_file():
        raise FileNotFoundError(f"GGUF model file not found: {model_path}")
    model_size = model_path.stat().st_size
    if model_size < MIN_MODEL_BYTES:
        raise ValueError(
            f"GGUF is unexpectedly small ({model_size:,} bytes); refusing to load it."
        )
    if not gguf_python_path.is_dir():
        raise FileNotFoundError(f"llama.cpp GGUF Python package not found: {gguf_python_path}")
    sys.path.insert(0, str(gguf_python_path))
    try:
        import gguf
    except ImportError as error:
        raise RuntimeError(
            f"Could not import the pinned llama.cpp GGUF reader: {error}"
        ) from error

    try:
        reader = gguf.GGUFReader(str(model_path))
        architecture = _field_value(reader, "general.architecture")
        file_type = _field_value(reader, "general.file_type")
        model_name = _field_value(reader, "general.name")
        template = _field_value(reader, "tokenizer.chat_template")
        tensor_count = len(reader.tensors)
        tensor_names = [tensor.name for tensor in reader.tensors]
        if architecture in {"granite", "granitehybrid"}:
            metadata_prefix = architecture
            head_count_kv = _field_value(
                reader, f"{metadata_prefix}.attention.head_count_kv"
            )
            validate_architecture_tensors(
                architecture,
                tensor_names,
                head_count_kv,
                int(_field_value(reader, f"{metadata_prefix}.block_count")),
            )
    except (OSError, ValueError, KeyError) as error:
        raise ValueError(f"Unable to read valid GGUF metadata from {model_path}: {error}") from error

    if architecture != EXPECTED_ARCHITECTURE:
        raise ValueError(
            f"Expected the converted Granite-Hybrid model, found {architecture!r}."
        )
    if int(file_type) != expected_file_type:
        raise ValueError(
            f"Expected GGUF file type {expected_file_type}, found {file_type!r}."
        )
    if not isinstance(template, str) or not all(
        marker in template for marker in REQUIRED_TEMPLATE_MARKERS
    ):
        raise ValueError(
            "The GGUF is missing a recognizable embedded chat template. "
            "Do not replace it with an invented template."
        )
    if tensor_count < 300:
        raise ValueError(
            f"GGUF contains only {tensor_count} tensors; expected the full 3B model."
        )

    return {
        "path": str(model_path.resolve()),
        "size_bytes": model_size,
        "architecture": architecture,
        "file_type": int(file_type),
        "model_name": model_name,
        "tensor_count": tensor_count,
        "chat_template_present": True,
        "weights_loaded": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect the local merged-model GGUF metadata without loading weights."
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--gguf-python", type=Path, required=True)
    parser.add_argument(
        "--expected-file-type",
        type=int,
        default=EXPECTED_FILE_TYPE,
        help="Expected GGUF file type (15 for Q4_K_M, 1 for F16).",
    )
    args = parser.parse_args()
    try:
        report = inspect_gguf(
            args.model,
            args.gguf_python,
            expected_file_type=args.expected_file_type,
        )
    except (FileNotFoundError, RuntimeError, ValueError) as error:
        print(f"GGUF preflight failed: {error}", file=sys.stderr)
        return 1
    for key, value in report.items():
        print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
