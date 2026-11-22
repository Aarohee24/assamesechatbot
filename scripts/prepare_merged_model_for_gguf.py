from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any


EXPECTED_ARCHITECTURE = "GraniteMoeHybridForCausalLM"
EXPECTED_MODEL_TYPE = "granitemoehybrid"
EXPECTED_VOCAB_SIZE = 100_352
EXPECTED_BASE_MODEL = "ptrdvn/kakugo-3B-asm"
EXPECTED_BASE_REVISION = "a6a854a0a680c4c57ec026df014f8f5964da8721"
WEIGHT_SHARDS = (
    "model-00001-of-00002.safetensors",
    "model-00002-of-00002.safetensors",
)
REQUIRED_FILES = (
    "config.json",
    "generation_config.json",
    *WEIGHT_SHARDS,
    "model.safetensors.index.json",
    "tokenizer.json",
    "tokenizer_config.json",
    "chat_template.jinja",
    "training_metadata.json",
)


class ModelPreparationError(RuntimeError):
    pass


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ModelPreparationError(f"Unable to read valid JSON from {path}: {error}") from error
    if not isinstance(value, dict):
        raise ModelPreparationError(f"Expected a JSON object in {path}.")
    return value


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def inspect_model(source: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (source / name).is_file()]
    if missing:
        raise ModelPreparationError(f"Merged model is missing required files: {missing}")

    config = _read_json(source / "config.json")
    metadata = _read_json(source / "training_metadata.json")
    index = _read_json(source / "model.safetensors.index.json")
    if (
        config.get("model_type") != EXPECTED_MODEL_TYPE
        or EXPECTED_ARCHITECTURE not in config.get("architectures", [])
    ):
        raise ModelPreparationError(
            "The merged checkpoint is not the expected GraniteMoeHybrid Kakugo model."
        )
    if config.get("vocab_size") != EXPECTED_VOCAB_SIZE:
        raise ModelPreparationError(
            f"Unexpected model vocabulary: {config.get('vocab_size')}."
        )
    if (
        metadata.get("merged") is not True
        or metadata.get("base_model") != EXPECTED_BASE_MODEL
        or metadata.get("base_revision") != EXPECTED_BASE_REVISION
    ):
        raise ModelPreparationError(
            "Training metadata does not confirm the requested merged Kakugo checkpoint."
        )
    if metadata.get("merge_method") != "Direct FP16 LoRA weight merge":
        raise ModelPreparationError("The training metadata does not describe the expected FP16 merge.")

    layer_types = config.get("layer_types")
    if not isinstance(layer_types, list) or len(layer_types) != config.get("num_hidden_layers"):
        raise ModelPreparationError("Model layer_types do not match num_hidden_layers.")
    if any(layer_type not in {"full_attention", "attention"} for layer_type in layer_types):
        raise ModelPreparationError(
            "The checkpoint contains non-attention layer types; this conversion workflow "
            "does not claim support for its Mamba/SSM layers."
        )

    weight_map = index.get("weight_map")
    if not isinstance(weight_map, dict) or not weight_map:
        raise ModelPreparationError("Safetensors index has no tensor weight map.")
    tensor_names = list(weight_map)
    if any("mamba" in name.casefold() or "ssm" in name.casefold() for name in tensor_names):
        raise ModelPreparationError(
            "Safetensors index contains Mamba/SSM tensors, so all-attention normalization "
            "would be unsafe."
        )

    layer_count = int(config["num_hidden_layers"])
    projection_counts = {
        projection: sum(
            name.endswith(f".self_attn.{projection}.weight") for name in tensor_names
        )
        for projection in ("q_proj", "k_proj", "v_proj", "o_proj")
    }
    if any(count != layer_count for count in projection_counts.values()):
        raise ModelPreparationError(
            f"Attention projection tensors do not match the {layer_count}-layer config: "
            f"{projection_counts}."
        )

    expected_size = index.get("metadata", {}).get("total_size")
    actual_size = sum((source / shard).stat().st_size for shard in WEIGHT_SHARDS)
    if (
        not isinstance(expected_size, int)
        or expected_size > actual_size
        or actual_size - expected_size > 1024 * 1024
    ):
        raise ModelPreparationError(
            "Safetensors tensor bytes do not fit within shard file sizes (including "
            f"headers): index says {expected_size}, files total {actual_size}."
        )

    return {
        "architecture": EXPECTED_ARCHITECTURE,
        "model_type": EXPECTED_MODEL_TYPE,
        "vocabulary_size": EXPECTED_VOCAB_SIZE,
        "parameter_count": index.get("metadata", {}).get("total_parameters"),
        "weight_bytes": actual_size,
        "layers": layer_count,
        "layer_types": sorted(set(layer_types)),
        "attention_projection_counts": projection_counts,
        "mamba_or_ssm_tensors": 0,
        "conversion_normalization": (
            "The local Transformers config calls the all-attention layers "
            "'full_attention'. The pinned llama.cpp converter recognizes 'attention'. "
            "Only in a separate hard-linked staging copy, normalize this equivalent "
            "all-attention enum. The converter then exports the same dense Granite "
            "weights under the granite GGUF architecture; no model weights are changed."
        ),
    }


def prepare_staging_copy(source: Path, staging: Path) -> dict[str, Any]:
    report = inspect_model(source)
    if staging.exists():
        staged_missing = [
            filename for filename in REQUIRED_FILES if not (staging / filename).is_file()
        ]
        if staged_missing:
            raise FileExistsError(
                f"Refusing to overwrite incomplete staging directory {staging}; "
                f"missing files: {staged_missing}"
            )
        staged_config = _read_json(staging / "config.json")
        expected_staged_config = _read_json(source / "config.json")
        expected_staged_config["layer_types"] = [
            "attention"
        ] * int(expected_staged_config["num_hidden_layers"])
        if staged_config != expected_staged_config:
            raise FileExistsError(
                f"Refusing to reuse staging directory with an unexpected config: {staging}"
            )
        for filename in REQUIRED_FILES:
            if filename == "config.json":
                continue
            if filename in WEIGHT_SHARDS:
                try:
                    same_file = os.path.samefile(source / filename, staging / filename)
                except OSError:
                    same_file = False
                if not same_file:
                    raise FileExistsError(
                        f"Staging shard is not hard-linked to the expected source file: "
                        f"{staging / filename}"
                    )
            elif _sha256(source / filename) != _sha256(staging / filename):
                raise FileExistsError(
                    f"Staging file differs from source; refusing reuse: {staging / filename}"
                )
        report.update(
            {
                "source_model": str(source.resolve()),
                "staging_model": str(staging.resolve()),
                "source_config_sha256": _sha256(source / "config.json"),
                "staging_config_sha256": _sha256(staging / "config.json"),
                "original_safetensors_are_hard_linked": True,
                "original_checkpoint_modified": False,
                "staging_reused": True,
            }
        )
        return report
    staging.parent.mkdir(parents=True, exist_ok=True)
    staging.mkdir()

    for filename in REQUIRED_FILES:
        destination = staging / filename
        source_file = source / filename
        if filename in WEIGHT_SHARDS:
            try:
                os.link(source_file, destination)
            except OSError as error:
                raise ModelPreparationError(
                    "Could not hard-link a safetensors shard into the staging directory. "
                    "Both directories must be on the same local volume; original weights "
                    f"were not copied or modified. {error}"
                ) from error
        else:
            shutil.copy2(source_file, destination)

    config = _read_json(staging / "config.json")
    config["layer_types"] = ["attention"] * int(config["num_hidden_layers"])
    (staging / "config.json").write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    report.update(
        {
            "source_model": str(source.resolve()),
            "staging_model": str(staging.resolve()),
            "source_config_sha256": _sha256(source / "config.json"),
            "staging_config_sha256": _sha256(staging / "config.json"),
            "original_safetensors_are_hard_linked": True,
            "original_checkpoint_modified": False,
            "staging_reused": False,
        }
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate and stage the local merged Kakugo checkpoint for llama.cpp conversion."
    )
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--staging", type=Path, required=True)
    args = parser.parse_args()
    report = prepare_staging_copy(args.source, args.staging)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
