import unittest

from scripts.extract_textbooks import _classify_page, _quality_text
from scripts.evaluate_assamese_ocr_samples import SAMPLE_PAGES, _assamese_stats


COPYRIGHT_ONLY_PAGE = "Copyright-SCERT, Assam \nnot to be republished"


class TextbookExtractionQualityTests(unittest.TestCase):
    def test_ocr_sample_is_fixed_and_bounded(self):
        self.assertEqual(len(SAMPLE_PAGES), 15)
        self.assertEqual(len({(book, page) for book, page, _ in SAMPLE_PAGES}), 15)

    def test_ocr_assamese_metrics_count_script_letters_without_claiming_accuracy(self):
        metrics = _assamese_stats("অসমীয়া ভাষা — CPU 123")

        self.assertGreater(metrics["assamese_block_letters"], 0)
        self.assertLess(metrics["assamese_block_letter_ratio"], 1)
        self.assertEqual(metrics["whitespace_words"], 5)
        self.assertEqual(metrics["replacement_characters"], 0)

    def test_empty_ocr_output_has_zero_script_ratio(self):
        metrics = _assamese_stats("")

        self.assertEqual(metrics["assamese_block_letter_ratio"], 0)
        self.assertEqual(metrics["whitespace_words"], 0)

    def test_quality_text_excludes_standalone_copyright_lines_only(self):
        text = f"{COPYRIGHT_ONLY_PAGE}\nঅসমৰ ইতিহাস\n"

        self.assertEqual(_quality_text(text), "অসমৰ ইতিহাস")
        self.assertIn(COPYRIGHT_ONLY_PAGE, text)

    def test_footer_only_assamese_page_is_flagged_for_visual_or_ocr_review(self):
        empty, ocr_candidate, encoding_suspect = _classify_page(
            COPYRIGHT_ONLY_PAGE,
            1,
            expected_assamese=True,
        )

        self.assertFalse(empty)
        self.assertTrue(ocr_candidate)
        self.assertFalse(encoding_suspect)

    def test_garbled_font_mapping_is_flagged_without_modifying_raw_text(self):
        garbled = "x\u0014x\u0014y" * 10

        _, ocr_candidate, encoding_suspect = _classify_page(
            garbled,
            1,
            expected_assamese=True,
        )

        self.assertTrue(ocr_candidate)
        self.assertTrue(encoding_suspect)

    def test_assamese_text_is_not_flagged_as_encoding_suspect(self):
        assamese_text = "অসমীয়া ভাষাৰ এই বাক্যটো যথেষ্ট দীঘল আৰু পঢ়িব পৰা।"

        _, ocr_candidate, encoding_suspect = _classify_page(
            assamese_text,
            0,
            expected_assamese=True,
        )

        self.assertFalse(ocr_candidate)
        self.assertFalse(encoding_suspect)

    def test_non_assamese_book_is_not_flagged_by_filename_assumption_alone(self):
        _, ocr_candidate, encoding_suspect = _classify_page(
            "An English page with enough readable extracted text for review.",
            0,
            expected_assamese=False,
        )

        self.assertFalse(ocr_candidate)
        self.assertFalse(encoding_suspect)
