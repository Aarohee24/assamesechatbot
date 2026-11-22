import json
import os
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_merged_model_for_gguf import (
    ModelPreparationError,
    REQUIRED_FILES,
    WEIGHT_SHARDS,
    inspect_model,
    prepare_staging_copy,
)


class MergedModelConversionTests(unittest.TestCase):
    def _create_model(self, root: Path) -> Path:
        model = root / "merged_model"
        model.mkdir()
        for filename in REQUIRED_FILES:
            (model / filename).write_bytes(b"fixture")

        config = {
            "architectures": ["GraniteMoeHybridForCausalLM"],
            "model_type": "granitemoehybrid",
            "vocab_size": 100352,
            "num_hidden_layers": 2,
            "layer_types": ["full_attention", "full_attention"],
        }
        (model / "config.json").write_text(json.dumps(config), encoding="utf-8")
        metadata = {
            "merged": True,
            "base_model": "ptrdvn/kakugo-3B-asm",
            "base_revision": "a6a854a0a680c4c57ec026df014f8f5964da8721",
            "merge_method": "Direct FP16 LoRA weight merge",
        }
        (model / "training_metadata.json").write_text(
            json.dumps(metadata), encoding="utf-8"
        )
        weight_map = {}
        for layer in range(2):
            for projection in ("q_proj", "k_proj", "v_proj", "o_proj"):
                weight_map[
                    f"model.layers.{layer}.self_attn.{projection}.weight"
                ] = WEIGHT_SHARDS[layer]
        index = {
            "metadata": {
                "total_parameters": 8,
                "total_size": sum((model / shard).stat().st_size for shard in WEIGHT_SHARDS),
            },
            "weight_map": weight_map,
        }
        (model / "model.safetensors.index.json").write_text(
            json.dumps(index), encoding="utf-8"
        )
        return model

    def test_preflight_validates_merged_checkpoint_without_loading_weights(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = self._create_model(Path(temporary))

            report = inspect_model(model)

        self.assertEqual(report["parameter_count"], 8)
        self.assertEqual(report["layer_types"], ["full_attention"])
        self.assertEqual(report["mamba_or_ssm_tensors"], 0)
        self.assertEqual(report["attention_projection_counts"]["q_proj"], 2)

    def test_staging_normalizes_config_and_preserves_original_weight_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = self._create_model(root)
            originals = {name: (model / name).read_bytes() for name in WEIGHT_SHARDS}
            staging = root / "models" / "stage"

            report = prepare_staging_copy(model, staging)

            staged_config = json.loads(
                (staging / "config.json").read_text(encoding="utf-8")
            )
            self.assertEqual(staged_config["layer_types"], ["attention", "attention"])
            self.assertEqual(
                {name: (model / name).read_bytes() for name in WEIGHT_SHARDS},
                originals,
            )
            if os.name == "nt":
                self.assertEqual(
                    os.stat(model / WEIGHT_SHARDS[0]).st_ino,
                    os.stat(staging / WEIGHT_SHARDS[0]).st_ino,
                )
            self.assertFalse(report["original_checkpoint_modified"])
            self.assertTrue(report["original_safetensors_are_hard_linked"])

    def test_rejects_mamba_or_unknown_layer_types(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            model = self._create_model(Path(temporary))
            config_path = model / "config.json"
            config = json.loads(config_path.read_text(encoding="utf-8"))
            config["layer_types"][0] = "mamba"
            config_path.write_text(json.dumps(config), encoding="utf-8")

            with self.assertRaisesRegex(ModelPreparationError, "non-attention"):
                inspect_model(model)

    def test_staging_refuses_to_overwrite_an_existing_incomplete_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = self._create_model(root)
            staging = root / "staging"
            staging.mkdir()

            with self.assertRaises(FileExistsError):
                prepare_staging_copy(model, staging)

    def test_staging_reuses_only_an_identical_existing_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            model = self._create_model(root)
            staging = root / "staging"
            first = prepare_staging_copy(model, staging)

            second = prepare_staging_copy(model, staging)

        self.assertFalse(first["staging_reused"])
        self.assertTrue(second["staging_reused"])


if __name__ == "__main__":
    unittest.main()
