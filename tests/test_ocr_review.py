import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.ocr_review import OCRReviewStore


class OCRReviewStoreTests(unittest.TestCase):
    def _make_store(self, root: Path) -> tuple[OCRReviewStore, dict]:
        book = "Example.pdf"
        source_path = "data/books/Example.pdf"
        text = "অসমীয়া মূল পাঠ।"
        metadata_path = (
            root
            / "data"
            / "ocr_text"
            / "runs"
            / "settings"
            / "pages"
            / "example"
            / "page-000001.json"
        )
        metadata_path.parent.mkdir(parents=True)
        metadata_path.write_text(
            json.dumps(
                {
                    "book": book,
                    "source_relative_path": source_path,
                    "source_pdf_sha256": "source-sha",
                    "page_number": 1,
                    "status": "completed",
                    "settings_id": "settings",
                    "text": text,
                    "confidence": {"mean": 77.0},
                    "review_flags": ["human_review_required"],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        page = {
            "book": book,
            "source_relative_path": source_path,
            "source_pdf_sha256": "source-sha",
            "page_number": 1,
            "ocr_status": "completed",
            "ocr_settings_id": "settings",
            "ocr_text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "review_status": "pending",
            "reviewed_by": "",
            "reviewed_at": "",
            "review_notes": "",
        }
        manifest_path = root / "data" / "training_data" / "ocr-review-manifest.json"
        manifest_path.parent.mkdir(parents=True)
        manifest_path.write_text(
            json.dumps({"version": 1, "pages": [page]}, ensure_ascii=False),
            encoding="utf-8",
        )
        store = OCRReviewStore(
            project_root=root,
            manifest_path=manifest_path,
            ocr_dir=root / "data" / "ocr_text",
            corrected_dir=root / "data" / "corrected_ocr",
        )
        return store, store.pages[0]

    def test_approval_is_persisted_with_corrected_unicode_and_backup(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            store, page = self._make_store(root)
            reviewed_at = store.update_review(
                page,
                status="approved",
                reviewer="reviewer",
                notes="Compared against PDF.",
                corrected_text="অসমীয়া সংশোধিত পাঠ।",
            )

            saved = json.loads(store.manifest_path.read_text(encoding="utf-8"))["pages"][0]
            self.assertEqual(saved["review_status"], "approved")
            self.assertEqual(saved["reviewed_by"], "reviewer")
            self.assertTrue(reviewed_at)
            self.assertEqual(saved["reviewed_at"], reviewed_at)
            self.assertEqual(saved["review_notes"], "Compared against PDF.")
            self.assertNotIn("text", saved)
            self.assertNotIn("_display_record", saved)
            self.assertIn("data/corrected_ocr/", saved["corrected_text_path"])
            self.assertEqual(store.reviewed_text(saved), "অসমীয়া সংশোধিত পাঠ।")
            self.assertTrue(
                (store.manifest_path.parent / "ocr-review-manifest.initial-backup.json").is_file()
            )
            self.assertNotEqual(
                saved["ocr_text_sha256"], saved["corrected_text_sha256"]
            )

    def test_pending_and_rejected_pages_do_not_save_edits_as_approved_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            store, page = self._make_store(Path(temporary))
            store.update_review(
                page,
                status="excluded",
                reviewer="reviewer",
                notes="Wrong language.",
                corrected_text="Edited text must not be used.",
            )
            saved = json.loads(store.manifest_path.read_text(encoding="utf-8"))["pages"][0]
            self.assertEqual(saved["review_status"], "excluded")
            self.assertNotIn("corrected_text_path", saved)
            self.assertEqual(store.reviewed_text(saved), "অসমীয়া মূল পাঠ।")

    def test_approval_requires_reviewer_and_nonempty_text(self):
        with tempfile.TemporaryDirectory() as temporary:
            store, page = self._make_store(Path(temporary))
            with self.assertRaisesRegex(ValueError, "Reviewer name"):
                store.update_review(
                    page,
                    status="approved",
                    reviewer=" ",
                    notes="",
                    corrected_text="অসমীয়া",
                )
            with self.assertRaisesRegex(ValueError, "empty OCR page"):
                store.update_review(
                    page,
                    status="approved",
                    reviewer="reviewer",
                    notes="",
                    corrected_text=" ",
                )
            self.assertEqual(page["review_status"], "pending")

    def test_corrected_text_integrity_is_checked_after_review(self):
        with tempfile.TemporaryDirectory() as temporary:
            store, page = self._make_store(Path(temporary))
            store.update_review(
                page,
                status="needs_correction",
                reviewer="reviewer",
                notes="Fix spelling.",
                corrected_text="সংশোধন কৰা অসমীয়া পাঠ।",
            )
            corrected_path = store.project_root / page["corrected_text_path"]
            corrected_path.write_text("changed outside review", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "changed after review"):
                store.reviewed_text(page)


if __name__ == "__main__":
    unittest.main()
