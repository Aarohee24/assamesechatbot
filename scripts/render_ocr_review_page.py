from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
from typing import Any

import pypdfium2 as pdfium


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_DIR = PROJECT_ROOT / "data" / "ocr_text"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "reports" / "ocr-human-review"
RENDER_DPI = 300


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_stem(value: str) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", Path(value).stem).strip(" .") or "book"


def _find_page_record(
    ocr_dir: Path,
    book_name: str,
    page_number: int,
) -> tuple[dict[str, Any], Path]:
    matches = []
    for metadata_path in ocr_dir.glob("runs/*/pages/*/page-*.json"):
        try:
            record = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            isinstance(record, dict)
            and record.get("book") == book_name
            and record.get("page_number") == page_number
            and record.get("status") == "completed"
        ):
            matches.append((record, metadata_path))
    if not matches:
        raise FileNotFoundError(
            f"No completed OCR metadata found for {book_name!r} page {page_number}."
        )
    identities = {
        (
            record.get("source_relative_path"),
            record.get("source_pdf_sha256"),
            record.get("settings_id"),
            hashlib.sha256(record.get("text", "").encode("utf-8")).hexdigest(),
        )
        for record, _ in matches
    }
    if len(identities) > 1:
        raise ValueError(
            "Multiple OCR versions exist for this page. Select/resolve the intended "
            "OCR run before human review."
        )
    return matches[-1]


def render_review_page(
    *,
    ocr_dir: Path,
    book_name: str,
    page_number: int,
    books_dir: Path,
    output_dir: Path,
) -> tuple[Path, Path]:
    if page_number < 1:
        raise ValueError("PDF page numbers are 1-based and must be positive.")
    record, metadata_path = _find_page_record(ocr_dir, book_name, page_number)
    relative_path = Path(record["source_relative_path"])
    pdf_path = relative_path if relative_path.is_absolute() else PROJECT_ROOT / relative_path
    if not pdf_path.is_file():
        pdf_path = books_dir / Path(book_name)
    if not pdf_path.is_file():
        raise FileNotFoundError(f"Original PDF not found for OCR page: {pdf_path}")
    actual_sha256 = _sha256(pdf_path)
    if actual_sha256 != record["source_pdf_sha256"]:
        raise ValueError(
            f"Original PDF hash no longer matches OCR source for {book_name}."
        )

    document = pdfium.PdfDocument(str(pdf_path))
    try:
        if page_number > len(document):
            raise ValueError(
                f"PDF has {len(document)} pages; requested page {page_number}."
            )
        page = document[page_number - 1]
        bitmap = page.render(scale=RENDER_DPI / 72)
        try:
            image = bitmap.to_pil()
            try:
                output_dir.mkdir(parents=True, exist_ok=True)
                base = (
                    f"{_safe_stem(book_name)}_{actual_sha256[:12]}_"
                    f"page-{page_number:06d}"
                )
                image_path = output_dir / f"{base}.png"
                image.save(image_path, format="PNG")
            finally:
                image.close()
        finally:
            bitmap.close()
    finally:
        document.close()

    report_path = output_dir / f"{base}.md"
    text = record.get("text", "")
    report_path.write_text(
        "\n".join(
            [
                f"# Human OCR review: {book_name}, PDF page {page_number}",
                "",
                f"- Original PDF: `{record['source_relative_path']}`",
                f"- Original PDF SHA-256: `{actual_sha256}`",
                f"- OCR metadata: `{metadata_path}`",
                f"- OCR settings ID: `{record['settings_id']}`",
                f"- OCR: Tesseract `{record.get('language')}`, OEM {record.get('oem')}, "
                f"PSM {record.get('psm')}, {record.get('render_dpi')} DPI",
                f"- Confidence: `{json.dumps(record.get('confidence', {}), ensure_ascii=False)}`",
                f"- Language identification: "
                f"`{json.dumps(record.get('language_identification', {}), ensure_ascii=False)}`",
                f"- Review flags: `{', '.join(record.get('review_flags', []))}`",
                f"- Retained page image: `{image_path}`",
                "",
                "Compare every OCR line with the rendered page. Do not treat confidence or language identification as correctness. Record approval/exclusion and reviewer information in the review manifest.",
                "",
                "```text",
                text or "[No text recognized]",
                "```",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return image_path, report_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render one OCR result and its original PDF page for human review."
    )
    parser.add_argument("--book", required=True, help="Exact PDF filename.")
    parser.add_argument("--page", required=True, type=int, help="1-based PDF page number.")
    parser.add_argument("--ocr-dir", type=Path, default=DEFAULT_OCR_DIR)
    parser.add_argument("--books-dir", type=Path, default=PROJECT_ROOT / "data" / "books")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()
    try:
        image_path, report_path = render_review_page(
            ocr_dir=args.ocr_dir,
            book_name=args.book,
            page_number=args.page,
            books_dir=args.books_dir,
            output_dir=args.output_dir,
        )
    except Exception as error:
        parser.exit(1, f"ERROR: {type(error).__name__}: {error}\n")
    print(f"PAGE_IMAGE={image_path}")
    print(f"REVIEW_REPORT={report_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
