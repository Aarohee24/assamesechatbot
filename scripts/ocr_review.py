from __future__ import annotations

from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import uuid
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "data" / "training_data" / "ocr-review-manifest.json"
DEFAULT_OCR_DIR = PROJECT_ROOT / "data" / "ocr_text"
DEFAULT_CORRECTED_DIR = PROJECT_ROOT / "data" / "corrected_ocr"
REVIEW_STATUSES = {"pending", "approved", "excluded", "needs_correction"}


def _page_key(page: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(page.get("source_relative_path", "")),
        str(page.get("source_pdf_sha256", "")),
        int(page.get("page_number", 0)),
    )


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)
    finally:
        temporary_path.unlink(missing_ok=True)


def _safe_book_stem(book: str) -> str:
    stem = re.sub(r'[<>:"/\\|?*]+', "_", Path(book).stem).strip(" .")
    return stem or "book"


class OCRReviewStore:
    def __init__(
        self,
        *,
        project_root: Path = PROJECT_ROOT,
        manifest_path: Path = DEFAULT_MANIFEST,
        ocr_dir: Path = DEFAULT_OCR_DIR,
        corrected_dir: Path = DEFAULT_CORRECTED_DIR,
    ) -> None:
        self.project_root = project_root.resolve()
        self.manifest_path = manifest_path.resolve()
        self.ocr_dir = ocr_dir.resolve()
        self.corrected_dir = corrected_dir.resolve()
        try:
            self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(
                f"Unable to load OCR review manifest {self.manifest_path}: {error}"
            ) from error
        if not isinstance(self.manifest, dict) or not isinstance(
            self.manifest.get("pages"), list
        ):
            raise ValueError(f"Invalid OCR review manifest: {self.manifest_path}")

        self._ocr_records: dict[tuple[str, str, int], dict[str, Any]] = {}
        self._load_ocr_records()
        self._validate_manifest_pages()

    def _load_ocr_records(self) -> None:
        paths = sorted(self.ocr_dir.glob("runs/*/pages/*/page-*.json"))
        if not paths:
            raise FileNotFoundError(f"No OCR page records found under {self.ocr_dir}")
        for path in paths:
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise RuntimeError(f"Unable to read OCR page metadata {path}: {error}") from error
            if not isinstance(record, dict):
                raise ValueError(f"OCR page metadata is not an object: {path}")
            key = _page_key(record)
            if not all(key) or key[2] < 1:
                raise ValueError(f"Invalid source identity in OCR metadata: {path}")
            previous = self._ocr_records.get(key)
            if previous is not None and (
                previous.get("settings_id") != record.get("settings_id")
                or _sha256_text(previous.get("text", "")) != _sha256_text(record.get("text", ""))
            ):
                raise ValueError(
                    "Multiple conflicting OCR versions exist for "
                    f"{key[0]} page {key[2]}; resolve the OCR run before review."
                )
            self._ocr_records[key] = record

    def _validate_manifest_pages(self) -> None:
        seen = set()
        for page in self.manifest["pages"]:
            if not isinstance(page, dict):
                raise ValueError("Every review manifest page must be an object.")
            key = _page_key(page)
            if not all(key) or key[2] < 1 or key in seen:
                raise ValueError(f"Invalid or duplicate page identity in manifest: {key}")
            seen.add(key)
            if page.get("review_status") not in REVIEW_STATUSES:
                raise ValueError(
                    f"Invalid review status {page.get('review_status')!r} for {key}."
                )

    @property
    def pages(self) -> list[dict[str, Any]]:
        return self.manifest["pages"]

    def ocr_record(self, page: dict[str, Any]) -> dict[str, Any]:
        key = _page_key(page)
        record = self._ocr_records.get(key)
        if record is None:
            raise FileNotFoundError(
                f"OCR metadata missing for {key[0]} page {key[2]}."
            )
        if (
            record.get("settings_id") != page.get("ocr_settings_id")
            or record.get("status") != page.get("ocr_status")
        ):
            raise ValueError(
                f"OCR metadata changed since manifest creation for {key[0]} page {key[2]}."
            )
        raw_text = record.get("text", "")
        if _sha256_text(raw_text) != page.get("ocr_text_sha256"):
            raise ValueError(
                f"OCR text changed since manifest creation for {key[0]} page {key[2]}."
            )
        return record

    def reviewed_text(self, page: dict[str, Any]) -> str:
        record = self.ocr_record(page)
        relative_path = page.get("corrected_text_path")
        if not relative_path:
            return record.get("text", "")
        path = (self.project_root / Path(relative_path)).resolve()
        if not path.is_relative_to(self.project_root):
            raise ValueError("Corrected OCR path must remain inside the project directory.")
        try:
            corrected_text = path.read_text(encoding="utf-8")
        except OSError as error:
            raise RuntimeError(f"Unable to read corrected OCR text {path}: {error}") from error
        if _sha256_text(corrected_text) != page.get("corrected_text_sha256"):
            raise ValueError(f"Corrected OCR text changed after review: {path}")
        return corrected_text

    def render_pdf_page(self, page: dict[str, Any]):
        import pypdfium2 as pdfium

        self.ocr_record(page)
        relative_path = Path(page["source_relative_path"])
        pdf_path = (
            relative_path
            if relative_path.is_absolute()
            else self.project_root / relative_path
        ).resolve()
        if not pdf_path.is_file():
            raise FileNotFoundError(f"Original PDF not found: {pdf_path}")
        digest = hashlib.sha256()
        with pdf_path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
        if digest.hexdigest() != page["source_pdf_sha256"]:
            raise ValueError(f"Original PDF hash changed since OCR: {pdf_path}")

        document = pdfium.PdfDocument(str(pdf_path))
        try:
            number = int(page["page_number"])
            if number > len(document):
                raise ValueError(f"PDF has {len(document)} pages; requested page {number}.")
            pdf_page = document[number - 1]
            bitmap = pdf_page.render(scale=300 / 72)
            try:
                return bitmap.to_pil().copy()
            finally:
                bitmap.close()
        finally:
            document.close()

    def _backup_manifest_once(self) -> Path:
        backup_path = self.manifest_path.with_name(
            f"{self.manifest_path.stem}.initial-backup{self.manifest_path.suffix}"
        )
        if not backup_path.exists():
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                with self.manifest_path.open("rb") as source, backup_path.open("xb") as target:
                    shutil.copyfileobj(source, target)
            except FileExistsError:
                pass
        return backup_path

    def _save_corrected_text(
        self, page: dict[str, Any], corrected_text: str
    ) -> tuple[str, str]:
        digest = _sha256_text(corrected_text)
        book_id = hashlib.sha256(
            page["source_relative_path"].encode("utf-8")
        ).hexdigest()[:10]
        directory = self.corrected_dir / str(page["ocr_settings_id"]) / (
            f"{_safe_book_stem(page['book'])}_{book_id}"
        )
        path = directory / f"page-{int(page['page_number']):06d}-{digest[:12]}.txt"
        directory.mkdir(parents=True, exist_ok=True)
        if path.exists():
            if _sha256_text(path.read_text(encoding="utf-8")) != digest:
                raise ValueError(f"Existing corrected OCR file has unexpected content: {path}")
        else:
            temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
            try:
                temporary_path.write_text(corrected_text, encoding="utf-8")
                try:
                    temporary_path.replace(path)
                except FileExistsError:
                    if _sha256_text(path.read_text(encoding="utf-8")) != digest:
                        raise
            finally:
                temporary_path.unlink(missing_ok=True)
        return path.relative_to(self.project_root).as_posix(), digest

    def update_review(
        self,
        page: dict[str, Any],
        *,
        status: str,
        reviewer: str,
        notes: str,
        corrected_text: str,
    ) -> str | None:
        if status not in {"approved", "excluded", "needs_correction"}:
            raise ValueError(f"Unsupported review action: {status!r}")
        if not reviewer.strip():
            raise ValueError("Reviewer name is required.")
        record = self.ocr_record(page)
        if status == "approved" and not corrected_text.strip():
            raise ValueError("An empty OCR page cannot be approved.")

        self._backup_manifest_once()
        page["review_status"] = status
        page["reviewed_by"] = reviewer.strip()
        page["reviewed_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        page["review_notes"] = notes.strip()
        if status in {"approved", "needs_correction"}:
            raw_text = record.get("text", "")
            if corrected_text != raw_text:
                corrected_path, corrected_digest = self._save_corrected_text(
                    page, corrected_text
                )
                page["corrected_text_path"] = corrected_path
                page["corrected_text_sha256"] = corrected_digest
            else:
                page.pop("corrected_text_path", None)
                page.pop("corrected_text_sha256", None)
        _atomic_write_json(self.manifest_path, self.manifest)
        return page.get("reviewed_at")
