import logging
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from scripts import ocr_textbooks


class OCRPilotTests(unittest.TestCase):
    def test_pilot_selects_fifty_pages_across_seventeen_books(self):
        inventory = [
            {"page_count": 100, "inventory_error": None}
            for _ in range(17)
        ]

        selected = ocr_textbooks._select_pilot_pages(inventory, 50)

        self.assertEqual(len(selected), 50)
        per_book = [sum(index == book_index for index, _ in selected) for book_index in range(17)]
        self.assertEqual(per_book.count(2), 1)
        self.assertEqual(per_book.count(3), 16)
        self.assertEqual(len(set(selected)), 50)

    def test_pilot_selection_is_spread_across_each_book(self):
        selected = ocr_textbooks._select_pilot_pages(
            [{"page_count": 100, "inventory_error": None}], 3
        )

        self.assertEqual([page for _, page in selected], [25, 50, 76])

    def test_pilot_respects_small_total_page_count(self):
        selected = ocr_textbooks._select_pilot_pages(
            [
                {"page_count": 1, "inventory_error": None},
                {"page_count": 2, "inventory_error": None},
            ],
            50,
        )

        self.assertEqual(selected, [(0, 1), (1, 1), (1, 2)])

    def test_tsv_confidence_uses_word_rows_and_ignores_negative_scores(self):
        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\t"
            "top\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t80.0\tঅসমীয়া\n"
            "5\t1\t1\t1\t1\t2\t10\t0\t10\t10\t40.0\tভাষা\n"
            "5\t1\t1\t1\t1\t3\t20\t0\t10\t10\t-1\t \n"
            "4\t1\t1\t1\t1\t0\t0\t0\t20\t10\t90.0\t\n"
        )

        self.assertEqual(
            ocr_textbooks._parse_tsv_confidence(tsv),
            {
                "word_count": 2,
                "mean": 60.0,
                "median": 60.0,
                "minimum": 40.0,
                "maximum": 80.0,
            },
        )

    def test_review_flags_cover_empty_low_confidence_english_and_mixed_text(self):
        empty_flags = ocr_textbooks._review_flags(
            "", {"mean": None}
        )
        english_flags = ocr_textbooks._review_flags(
            "This is a sufficiently long English-only OCR result.",
            {"mean": 55.0},
        )
        mixed_flags = ocr_textbooks._review_flags(
            "অসমীয়া ভাষা CPU API 123",
            {"mean": 95.0},
        )

        self.assertIn("empty_ocr", empty_flags)
        self.assertIn("low_confidence", english_flags)
        self.assertIn("english_only_candidate", english_flags)
        self.assertNotIn("english_only_candidate", mixed_flags)
        self.assertIn("human_review_required", mixed_flags)

    def test_classifier_english_label_flags_assamese_script_garbling(self):
        class FakeModel:
            def predict(self, text, k):
                return ["__label__eng_Latn"], [0.38]

        text = "]]8৞6 ৞00] ])691'0 01 (650 100126 )3[)169?7"
        language = ocr_textbooks._classify_page_language(FakeModel(), text)
        flags = ocr_textbooks._review_flags(text, {"mean": 40.0}, language)

        self.assertEqual(language["label"], "eng_Latn")
        self.assertIn("english_only_candidate", flags)
        self.assertIn("language_uncertain", flags)

    def test_only_completed_matching_pages_are_reused(self):
        record = {
            "status": "completed",
            "source_pdf_sha256": "abc",
            "settings_id": "settings",
        }

        self.assertTrue(
            ocr_textbooks._record_is_reusable(
                record, source_sha256="abc", settings_id="settings"
            )
        )
        self.assertFalse(
            ocr_textbooks._record_is_reusable(
                {**record, "status": "failed"},
                source_sha256="abc",
                settings_id="settings",
            )
        )
        self.assertFalse(
            ocr_textbooks._record_is_reusable(
                record, source_sha256="changed", settings_id="settings"
            )
        )

    def test_page_retries_after_transient_ocr_failure(self):
        class FakeImage:
            def save(self, path, format):
                Path(path).write_bytes(b"test image")

            def close(self):
                pass

        class FakeBitmap:
            width = 300
            height = 400

            def to_pil(self):
                return FakeImage()

            def close(self):
                pass

        class FakePage:
            def render(self, scale):
                return FakeBitmap()

        class FakeDocument:
            def __getitem__(self, index):
                return FakePage()

        tsv = (
            "level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\t"
            "top\twidth\theight\tconf\ttext\n"
            "5\t1\t1\t1\t1\t1\t0\t0\t10\t10\t90.0\tঅসমীয়া\n"
        )
        transient_error = subprocess.TimeoutExpired("tesseract", 1)
        runner_results = [
            transient_error,
            ("অসমীয়া ভাষা।", "", 0.1, 1000),
            (tsv, "", 0.1, 1000),
        ]

        with patch.object(
            ocr_textbooks,
            "_run_tesseract",
            side_effect=runner_results,
        ) as runner:
            record = ocr_textbooks._process_page(
                document=FakeDocument(),
                book={
                    "book": "Example.pdf",
                    "source_relative_path": "data/books/Example.pdf",
                    "source_pdf_size_bytes": 1,
                    "source_pdf_sha256": "abc",
                    "page_count": 1,
                    "pdf_metadata": {},
                },
                page_number=1,
                settings_id="settings",
                image_path=None,
                tesseract_path=Path("tesseract.exe"),
                timeout_seconds=1,
                max_attempts=2,
                logger=logging.getLogger("test_assamese_ocr"),
                language_model=None,
            )

        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["attempt_count"], 2)
        self.assertEqual(len(record["errors"]), 1)
        self.assertEqual(runner.call_count, 3)
        self.assertEqual(record["text"], "অসমীয়া ভাষা।")


if __name__ == "__main__":
    unittest.main()
