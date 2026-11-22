import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.check_gguf_model import inspect_gguf, validate_architecture_tensors


class GgufModelCheckTests(unittest.TestCase):
    def test_rejects_hybrid_metadata_that_marks_attention_layers_as_recurrent(self) -> None:
        with self.assertRaisesRegex(
            ValueError,
            "metadata marks all 40 layers as recurrent.*contains no SSM tensors",
        ):
            validate_architecture_tensors(
                "granitehybrid",
                ["blk.0.attn_q.weight", "blk.0.ffn_gate.weight"],
                [0] * 40,
                40,
            )

    def test_accepts_dense_granite_metadata_with_all_attention_tensors(self) -> None:
        suffixes = (
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
        tensor_names = [
            f"blk.{layer}.{suffix}"
            for layer in range(2)
            for suffix in suffixes
        ]
        validate_architecture_tensors(
            "granite",
            tensor_names,
            [8] * 2,
            2,
        )

    def test_rejects_dense_granite_with_missing_attention_tensors(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required.*blk.0.attn_k.weight"):
            validate_architecture_tensors(
                "granite",
                ["blk.0.attn_q.weight"],
                [8],
                1,
            )

    def test_rejects_missing_model_without_attempting_a_load(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(FileNotFoundError):
                inspect_gguf(root / "missing.gguf", root)

    def test_inspects_the_actual_merged_gguf_and_template_without_loading_weights(self) -> None:
        project = Path(__file__).resolve().parents[1]
        model = project / "models" / "assamese-q4_k_m.gguf"
        gguf_python = project / "tools" / "llama.cpp" / "gguf-py"
        if not model.is_file() or not (gguf_python / "gguf").is_dir():
            self.skipTest("Local GGUF or pinned llama.cpp metadata parser is unavailable.")

        with self.assertRaisesRegex(
            ValueError,
            "metadata marks all 40 layers as recurrent.*contains no SSM tensors",
        ):
            inspect_gguf(model, gguf_python)


if __name__ == "__main__":
    unittest.main()
