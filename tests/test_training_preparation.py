import json
from pathlib import Path
import tempfile
import unittest

from scripts.train_continued_pretraining import (
    _get_args,
    _make_blocks,
    _read_jsonl,
)


class FakeTokenizer:
    eos_token_id = 99

    def encode(self, text: str, add_special_tokens: bool = False) -> list[int]:
        return [ord(character) for character in text]


class TrainingPreparationTests(unittest.TestCase):
    def test_packed_token_blocks_keep_source_books_separate(self):
        rows = [
            {"source_relative_path": "book-a", "page_number": 2, "text": "cd"},
            {"source_relative_path": "book-a", "page_number": 1, "text": "ab"},
            {"source_relative_path": "book-b", "page_number": 1, "text": "XY"},
        ]
        blocks, metrics = _make_blocks(rows, FakeTokenizer(), sequence_length=3)

        self.assertEqual(
            blocks,
            [
                [ord("a"), ord("b"), 99],
                [ord("c"), ord("d"), 99],
                [ord("X"), ord("Y"), 99],
            ],
        )
        self.assertEqual(metrics["source_books"], 2)
        self.assertEqual(metrics["discarded_tail_tokens"], 0)

    def test_jsonl_loader_rejects_missing_source_book_and_blank_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "train.jsonl"
            path.write_text(json.dumps({"text": "text"}), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing source book"):
                _read_jsonl(path)
            path.write_text(
                json.dumps({"text": " ", "source_relative_path": "book"}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "empty training text"):
                _read_jsonl(path)

    def test_training_is_opt_in(self):
        args = _get_args(["--allow-automatic-ocr"])
        self.assertFalse(args.execute)
        self.assertTrue(args.allow_automatic_ocr)


if __name__ == "__main__":
    unittest.main()
