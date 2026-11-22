import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.automatic_corpus import build_automatic_corpus


ASSAMESE_TEXT = (
    "অসমীয়া ভাষাৰ এই পাঠটো বিদ্যালয়ৰ শিক্ষাৰ্থীৰ বাবে লিখা হৈছে। "
    "ইয়াত বিষয়টো সহজকৈ বুজোৱা হৈছে আৰু উদাহৰণো দিয়া হৈছে। "
    "শিক্ষাৰ্থীয়ে মনোযোগেৰে পঢ়িলে কথাখিনি বুজিব পাৰিব। "
    "এই পাঠত বিজ্ঞান, গণিত, ১২৩, CPU আৰু APIৰ কথাও আছে।"
)


class AutomaticCorpusTests(unittest.TestCase):
    def _create_input(self, root: Path, entries: list[dict]) -> tuple[Path, Path, bytes]:
        ocr_dir = root / "data" / "ocr_text"
        manifest_path = root / "data" / "training_data" / "ocr-review-manifest.json"
        records = []
        manifest_pages = []
        for index, entry in enumerate(entries):
            book = entry.get("book", f"Book {index}.pdf")
            source_path = f"data/books/{book}"
            page_number = entry.get("page_number", 1)
            text = entry.get("text", ASSAMESE_TEXT + f" অধ্যায় {index}।")
            sha = hashlib.sha256(book.encode("utf-8")).hexdigest()
            record = {
                "book": book,
                "source_relative_path": source_path,
                "source_pdf_sha256": sha,
                "page_number": page_number,
                "status": entry.get("status", "completed"),
                "settings_id": "test-settings",
                "text": text,
                "confidence": {"mean": entry.get("confidence", 80.0)},
                "language_identification": {
                    "status": entry.get("language_status", "classified"),
                    "label": entry.get("label", "asm_Beng"),
                    "confidence": 0.99,
                },
                "review_flags": entry.get("flags", ["human_review_required"]),
            }
            page_dir = (
                ocr_dir
                / "runs"
                / "test-settings"
                / "pages"
                / f"book-{index}"
            )
            page_dir.mkdir(parents=True, exist_ok=True)
            (page_dir / f"page-{page_number:06d}.json").write_text(
                json.dumps(record, ensure_ascii=False), encoding="utf-8"
            )
            records.append(record)
            manifest_pages.append(
                {
                    "book": book,
                    "source_relative_path": source_path,
                    "source_pdf_sha256": sha,
                    "page_number": page_number,
                    "ocr_status": record["status"],
                    "ocr_settings_id": "test-settings",
                    "ocr_text_sha256": hashlib.sha256(
                        text.encode("utf-8")
                    ).hexdigest(),
                    "review_status": entry.get("review_status", "pending"),
                }
            )
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_bytes = (
            json.dumps(
                {"version": 1, "pages": manifest_pages},
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        ).encode("utf-8")
        manifest_path.write_bytes(manifest_bytes)
        return ocr_dir, manifest_path, manifest_bytes

    def test_auto_filtering_preserves_manifest_and_creates_book_disjoint_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            entries = [
                {"book": "Book 0.pdf", "page_number": 1, "text": ASSAMESE_TEXT},
                {
                    "book": "Book 0.pdf",
                    "page_number": 2,
                    "text": ASSAMESE_TEXT,
                },
                {
                    "book": "Book 1.pdf",
                    "confidence": 45.0,
                    "text": ASSAMESE_TEXT + " CPU-ৰ সহায়ত।",
                },
                {"book": "Book 2.pdf", "text": ASSAMESE_TEXT + " অধ্যায় দুই।"},
                {"book": "Book 3.pdf", "text": ASSAMESE_TEXT + " অধ্যায় তিনি।"},
                {
                    "book": "English.pdf",
                    "text": "This page contains only English text and technical terms. " * 5,
                    "label": "eng_Latn",
                    "flags": ["english_only_candidate"],
                },
                {
                    "book": "Bengali.pdf",
                    "text": "বাংলা ভাষাৰ বাক্য আৰু পাঠ্যৰ উদাহৰণ এই পৃষ্ঠাত লিখা হৈছে। " * 4,
                    "label": "ben_Beng",
                    "flags": ["bengali_or_non_assamese_candidate"],
                },
                {
                    "book": "Bengali Medium Class.pdf",
                    "text": ASSAMESE_TEXT + " এই পৃষ্ঠাত অসমীয়া সদৃশ পাঠ আছে।",
                    "label": "asm_Beng",
                },
                {"book": "Empty.pdf", "text": "", "label": None, "language_status": "empty"},
            ]
            ocr_dir, manifest_path, original_manifest = self._create_input(root, entries)

            report = build_automatic_corpus(
                ocr_dir=ocr_dir,
                manifest_path=manifest_path,
                training_data_dir=manifest_path.parent,
                reports_dir=root / "reports",
                tokenizer_dir=root / "missing-tokenizer",
                validation_fraction=0.25,
            )

            self.assertEqual(manifest_path.read_bytes(), original_manifest)
            self.assertFalse(report["manifest_modified"])
            self.assertEqual(report["total_pages"], len(entries))
            self.assertEqual(report["automatic_split_status"], "created")
            self.assertEqual(report["accepted_pages"], 4)
            self.assertEqual(report["duplicate_pages_rejected"], 1)
            self.assertEqual(report["empty_pages"], 1)

            split_manifest = json.loads(
                Path(report["paths"]["split_manifest"]).read_text(encoding="utf-8")
            )
            book_splits = {book["source_relative_path"]: book["split"] for book in split_manifest["books"]}
            self.assertEqual(len(book_splits), 4)
            self.assertEqual(set(book_splits.values()), {"train", "validation"})

            accepted = [
                json.loads(line)
                for line in Path(report["paths"]["accepted_jsonl"])
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            rejected = [
                json.loads(line)
                for line in Path(report["paths"]["rejected_jsonl"])
                .read_text(encoding="utf-8")
                .splitlines()
            ]
            self.assertEqual(len(accepted), 4)
            self.assertEqual(len(rejected), 5)
            self.assertTrue(all(item["review_status_at_filter_time"] == "pending" for item in accepted))
            self.assertTrue(
                any("duplicate_page" in item["rejection_reasons"] for item in rejected)
            )
            self.assertTrue(
                any("bengali_or_non_assamese_candidate" in item["rejection_reasons"] for item in rejected)
            )
            self.assertTrue(
                any("non_assamese_medium_book" in item["rejection_reasons"] for item in rejected)
            )
            self.assertTrue(
                Path(report["paths"]["processed_train_jsonl"]).is_file()
            )
            self.assertTrue(
                Path(report["paths"]["processed_validation_jsonl"]).is_file()
            )
            self.assertEqual(report["tokenizer"]["status"], "approximate")

    def test_too_few_usable_books_does_not_invent_split_and_existing_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            ocr_dir, manifest_path, original_manifest = self._create_input(
                root, [{"book": "Only book.pdf", "text": ASSAMESE_TEXT}]
            )
            report = build_automatic_corpus(
                ocr_dir=ocr_dir,
                manifest_path=manifest_path,
                training_data_dir=manifest_path.parent,
                reports_dir=root / "reports",
                tokenizer_dir=root / "missing-tokenizer",
            )
            self.assertEqual(report["automatic_split_status"], "not_created")
            self.assertIsNone(report["paths"]["processed_train_jsonl"])
            self.assertFalse((manifest_path.parent / "processed").exists())
            self.assertEqual(manifest_path.read_bytes(), original_manifest)

            accepted_path = manifest_path.parent / "auto_filtered_assamese.txt"
            original_accepted = accepted_path.read_text(encoding="utf-8")
            with self.assertRaises(FileExistsError):
                build_automatic_corpus(
                    ocr_dir=ocr_dir,
                    manifest_path=manifest_path,
                    training_data_dir=manifest_path.parent,
                    reports_dir=root / "reports",
                    tokenizer_dir=root / "missing-tokenizer",
                )
            self.assertEqual(accepted_path.read_text(encoding="utf-8"), original_accepted)


if __name__ == "__main__":
    unittest.main()
