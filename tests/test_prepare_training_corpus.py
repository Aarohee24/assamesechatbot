import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.prepare_training_corpus import (
    _assign_book_splits,
    _character_distribution,
    _word_tokens,
    build_training_corpus,
    create_review_manifest,
)


class PrepareTrainingCorpusTests(unittest.TestCase):
    def test_unicode_text_metrics_preserve_assamese_marks_and_numbers(self):
        text = "অসমীয়া CPU ১২৩, 42।"
        distribution = _character_distribution(text)

        self.assertIn("assamese_bengali_unicode_block", distribution)
        self.assertIn("combining_marks", distribution)
        self.assertIn("numbers", distribution)
        self.assertIn("punctuation", distribution)
        self.assertIn("cpu", _word_tokens(text))

    def test_validation_split_is_by_book_and_deterministic(self):
        book_ids = [f"book-{index}.pdf" for index in range(10)]

        first = _assign_book_splits(book_ids, 0.1)
        second = _assign_book_splits(book_ids, 0.1)

        self.assertEqual(first, second)
        self.assertEqual(set(first.values()), {"train", "validation"})
        self.assertEqual(len(first), len(set(first)))

    def test_review_manifest_starts_all_pages_pending_and_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            page_path = (
                root
                / "ocr"
                / "runs"
                / "settings"
                / "pages"
                / "sample"
                / "page-000001.json"
            )
            page_path.parent.mkdir(parents=True)
            page_text = "অসমীয়া বাক্য।"
            page_path.write_text(
                json.dumps(
                    {
                        "book": "Example.pdf",
                        "source_relative_path": "data/books/Example.pdf",
                        "source_pdf_sha256": "abc123",
                        "page_number": 1,
                        "status": "completed",
                        "settings_id": "settings",
                        "text": page_text,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            manifest_path = root / "review.json"

            count = create_review_manifest(root / "ocr", manifest_path)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(count, 1)
            self.assertEqual(manifest["pages"][0]["review_status"], "pending")
            self.assertEqual(
                manifest["pages"][0]["ocr_text_sha256"],
                hashlib.sha256(page_text.encode("utf-8")).hexdigest(),
            )
            with self.assertRaises(FileExistsError):
                create_review_manifest(root / "ocr", manifest_path)

    def test_no_approved_pages_never_create_cleaned_corpus(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ocr_root = root / "ocr"
            page_path = (
                ocr_root
                / "runs"
                / "settings"
                / "pages"
                / "sample"
                / "page-000001.json"
            )
            page_path.parent.mkdir(parents=True)
            text = "অসমীয়া বাক্য।"
            page = {
                "book": "Example.pdf",
                "source_relative_path": "data/books/Example.pdf",
                "source_pdf_sha256": "abc123",
                "page_number": 1,
                "status": "completed",
                "settings_id": "settings",
                "text": text,
            }
            page_path.write_text(json.dumps(page, ensure_ascii=False), encoding="utf-8")
            manifest_path = root / "review.json"
            create_review_manifest(ocr_root, manifest_path)

            with self.assertRaisesRegex(ValueError, "No human-reviewed pages"):
                build_training_corpus(
                    ocr_dir=ocr_root,
                    manifest_path=manifest_path,
                    output_dir=root / "cleaned",
                    reports_dir=root / "reports",
                    tokenizer_dir=root / "tokenizer",
                    validation_fraction=0.1,
                )
            self.assertFalse((root / "cleaned").exists())

    def test_reviewed_corpus_keeps_books_disjoint_and_preserves_page_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ocr_root = root / "ocr"
            records = []
            for index in range(6):
                book_name = f"Book {index}.pdf"
                source_path = f"data/books/{book_name}"
                text = f"অসমীয়া পাঠ {index}। CPU ১২৩"
                page_path = (
                    ocr_root
                    / "runs"
                    / "settings"
                    / "pages"
                    / f"book-{index}"
                    / "page-000001.json"
                )
                page_path.parent.mkdir(parents=True, exist_ok=True)
                record = {
                    "book": book_name,
                    "source_relative_path": source_path,
                    "source_pdf_sha256": f"sha-{index}",
                    "page_number": 1,
                    "status": "completed",
                    "settings_id": "settings",
                    "text": text,
                }
                page_path.write_text(
                    json.dumps(record, ensure_ascii=False), encoding="utf-8"
                )
                records.append(record)

            manifest_path = root / "review.json"
            create_review_manifest(ocr_root, manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in manifest["pages"]:
                item["reviewed_by"] = "reviewer"
                item["reviewed_at"] = "2026-10-31T12:00:00+05:30"
                item["review_notes"] = "Compared against the original PDF page."
                if item["book"] == "Book 0.pdf":
                    item["review_status"] = "excluded"
                    continue
                item["review_status"] = "approved"
                item["corrected_text_path"] = (
                    f"data/corrected_ocr/{Path(item['book']).stem}.txt"
                )
                item["corrected_text_sha256"] = hashlib.sha256(
                    f"সংশোধিত পাঠ {Path(item['book']).stem}".encode("utf-8")
                ).hexdigest()
                corrected_path = root / item["corrected_text_path"]
                corrected_path.parent.mkdir(parents=True, exist_ok=True)
                corrected_path.write_text(
                    f"সংশোধিত পাঠ {Path(item['book']).stem}", encoding="utf-8"
                )
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
            )

            report = build_training_corpus(
                ocr_dir=ocr_root,
                manifest_path=manifest_path,
                output_dir=root / "cleaned",
                reports_dir=root / "reports",
                tokenizer_dir=root / "tokenizer",
                validation_fraction=0.1,
            )

            self.assertGreater(report["train_pages"], 0)
            self.assertGreater(report["validation_pages"], 0)
            self.assertEqual(report["rejected_page_count"], 1)
            self.assertEqual(
                {book["split"] for book in report["books"]},
                {"train", "validation"},
            )
            self.assertTrue(
                all(len(book["approved_page_numbers"]) == 1 for book in report["books"])
            )
            for book in report["books"]:
                output = Path(book["output_path"]).read_text(encoding="utf-8")
                index = int(Path(book["book"]).stem.split()[-1])
                self.assertIn(f"সংশোধিত পাঠ Book {index}", output)
                self.assertNotIn(f"অসমীয়া পাঠ {index}। CPU ১২৩", output)
                self.assertNotIn("[BOOK: Book 0.pdf", output)
            self.assertEqual(report["tokenizer_counts"]["status"], "unavailable")

            with self.assertRaises(FileExistsError):
                build_training_corpus(
                    ocr_dir=ocr_root,
                    manifest_path=manifest_path,
                    output_dir=root / "cleaned",
                    reports_dir=root / "reports",
                    tokenizer_dir=root / "tokenizer",
                    validation_fraction=0.1,
                )

    def test_approval_is_rejected_if_ocr_text_changed_after_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ocr_root = root / "ocr"
            for index in range(2):
                page_path = (
                    ocr_root
                    / "runs"
                    / "settings"
                    / "pages"
                    / f"book-{index}"
                    / "page-000001.json"
                )
                page_path.parent.mkdir(parents=True, exist_ok=True)
                page_path.write_text(
                    json.dumps(
                        {
                            "book": f"Book {index}.pdf",
                            "source_relative_path": f"data/books/Book {index}.pdf",
                            "source_pdf_sha256": f"sha-{index}",
                            "page_number": 1,
                            "status": "completed",
                            "settings_id": "settings",
                            "text": "Original OCR text",
                        }
                    ),
                    encoding="utf-8",
                )
            manifest_path = root / "review.json"
            create_review_manifest(ocr_root, manifest_path)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for item in manifest["pages"]:
                item["review_status"] = "approved"
                item["reviewed_by"] = "reviewer"
                item["reviewed_at"] = "2026-10-31T12:00:00+05:30"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False), encoding="utf-8"
            )
            page_path = next(ocr_root.glob("runs/*/pages/book-0/page-*.json"))
            page = json.loads(page_path.read_text(encoding="utf-8"))
            page["text"] = "Changed OCR text"
            page_path.write_text(json.dumps(page), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "OCR text changed"):
                build_training_corpus(
                    ocr_dir=ocr_root,
                    manifest_path=manifest_path,
                    output_dir=root / "cleaned",
                    reports_dir=root / "reports",
                    tokenizer_dir=root / "tokenizer",
                    validation_fraction=0.1,
                )


if __name__ == "__main__":
    unittest.main()
