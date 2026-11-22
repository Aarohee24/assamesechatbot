from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
import logging
from pathlib import Path
import re
import sys
from typing import Any
import warnings

from pypdf import PdfReader


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOKS_DIR = PROJECT_ROOT / "data" / "books"
DEFAULT_EXTRACTED_DIR = PROJECT_ROOT / "data" / "extracted_text"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"
REQUIRED_DIRECTORIES = (
    PROJECT_ROOT / "data" / "books",
    PROJECT_ROOT / "data" / "extracted_text",
    PROJECT_ROOT / "data" / "cleaned_text",
    PROJECT_ROOT / "data" / "training_data",
    DEFAULT_REPORTS_DIR,
    PROJECT_ROOT / "scripts",
    PROJECT_ROOT / "checkpoints",
)
OCR_TEXT_THRESHOLD = 20
COPYRIGHT_LINE_PATTERN = re.compile(
    r"^\s*copyright\s*[-,:]?\s*scert,?\s*assam\s*$|"
    r"^\s*not\s+(?:to\s+)?be\s+republished\s*$",
    re.IGNORECASE | re.MULTILINE,
)


class _ParserWarningHandler(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(self.format(record))


def _normalized_for_duplicate_check(text: str) -> str:
    return " ".join(text.split()).casefold()


def _quality_text(text: str) -> str:
    return COPYRIGHT_LINE_PATTERN.sub("", text).strip()


def _counts(text: str) -> dict[str, int]:
    return {
        "characters": len(text),
        "words": len(text.split()),
        "whitespace_tokens_estimate": len(text.split()),
    }


def _image_count(page: Any) -> tuple[int | None, str | None]:
    try:
        return len(page.images), None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def _classify_page(
    text: str,
    image_count: int | None,
    *,
    expected_assamese: bool,
) -> tuple[bool, bool, bool]:
    content = _quality_text(text)
    visible_chars = len(content)
    empty_extraction = visible_chars == 0 and image_count == 0
    has_assamese_script = any("\u0980" <= character <= "\u09ff" for character in content)
    has_suspicious_control = any(
        (ord(character) < 32 and character not in "\r\n\t")
        or character == "\ufffd"
        for character in content
    )
    encoding_suspect = has_suspicious_control or (
        expected_assamese
        and visible_chars >= OCR_TEXT_THRESHOLD
        and not has_assamese_script
    )
    low_text_with_visual_content = visible_chars < OCR_TEXT_THRESHOLD and (
        image_count is None or image_count > 0
    )
    no_extractable_assamese = expected_assamese and visible_chars < OCR_TEXT_THRESHOLD
    ocr_candidate = encoding_suspect or low_text_with_visual_content or no_extractable_assamese
    return empty_extraction, ocr_candidate, encoding_suspect


def _extract_book(pdf_path: Path, books_dir: Path, output_dir: Path) -> dict[str, Any]:
    relative_path = pdf_path.relative_to(books_dir)
    output_stem = re.sub(r'[<>:"/\\|?*]+', "_", relative_path.with_suffix("").as_posix())
    text_path = output_dir / f"{output_stem}.txt"
    metadata_path = output_dir / f"{output_stem}.json"
    text_path.parent.mkdir(parents=True, exist_ok=True)

    book: dict[str, Any] = {
        "book": pdf_path.name,
        "source_relative_path": relative_path.as_posix(),
        "source_size_bytes": pdf_path.stat().st_size,
        "page_count": 0,
        "text_path": str(text_path),
        "metadata_path": str(metadata_path),
        "pages": [],
        "book_errors": [],
        "parser_warnings": [],
    }
    filename = pdf_path.name.casefold()
    book["expected_assamese_text"] = (
        "assamese" in filename
        and "bengali medium" not in filename
        and "arabic (l4)" not in filename
    )
    warning_handler = _ParserWarningHandler()
    pypdf_logger = logging.getLogger("pypdf")
    pypdf_logger.addHandler(warning_handler)
    try:
        with warnings.catch_warnings(record=True) as captured_warnings:
            warnings.simplefilter("always")
            try:
                reader = PdfReader(str(pdf_path), strict=False)
                book["page_count"] = len(reader.pages)
                info = reader.metadata
                book["pdf_metadata"] = {
                    str(key): str(value) if value is not None else None
                    for key, value in (info or {}).items()
                }
            except Exception as error:
                book["book_errors"].append(
                    f"Unable to read PDF: {type(error).__name__}: {error}"
                )
                book["parser_warnings"] = [str(item.message) for item in captured_warnings]
                metadata_path.write_text(
                    json.dumps(book, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                return book

            extracted_pages: list[str] = []
            for page_index, page in enumerate(reader.pages, start=1):
                page_data: dict[str, Any] = {
                    "page_number": page_index,
                    "text": "",
                    "image_count": None,
                    "image_inspection_error": None,
                    "extraction_error": None,
                }
                page_data["image_count"], page_data["image_inspection_error"] = _image_count(page)
                try:
                    page_data["text"] = page.extract_text() or ""
                except Exception as error:
                    page_data["extraction_error"] = f"{type(error).__name__}: {error}"
                page_text = page_data["text"]
                content = _quality_text(page_text)
                counts = _counts(page_text)
                empty, ocr_candidate, encoding_suspect = _classify_page(
                    page_text,
                    page_data["image_count"],
                    expected_assamese=book["expected_assamese_text"],
                )
                normalized = _normalized_for_duplicate_check(content)
                page_data.update(
                    {
                        **counts,
                        "quality_text_characters": len(content),
                        "empty": empty,
                        "ocr_candidate": ocr_candidate,
                        "encoding_suspect": encoding_suspect,
                        "duplicate_sha256": (
                            hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                            if normalized
                            else None
                        ),
                    }
                )
                book["pages"].append(page_data)
                extracted_pages.append(f"[PAGE {page_index}]\n{page_text}")
            book["parser_warnings"] = [
                str(item.message) for item in captured_warnings
            ] + warning_handler.messages
    finally:
        pypdf_logger.removeHandler(warning_handler)

    text_path.write_text("\n\n".join(extracted_pages) + "\n", encoding="utf-8")
    book["counts"] = _counts("\n".join(page["text"] for page in book["pages"]))
    book["quality_text_characters"] = sum(
        page["quality_text_characters"] for page in book["pages"]
    )
    book["empty_page_numbers"] = [
        page["page_number"] for page in book["pages"] if page["empty"]
    ]
    book["ocr_candidate_page_numbers"] = [
        page["page_number"] for page in book["pages"] if page["ocr_candidate"]
    ]
    book["unreadable_pages"] = [
        {
            "page_number": page["page_number"],
            "error": page["extraction_error"],
        }
        for page in book["pages"]
        if page["extraction_error"]
    ]
    book["encoding_suspect_page_numbers"] = [
        page["page_number"] for page in book["pages"] if page["encoding_suspect"]
    ]
    book["image_inspection_errors"] = [
        {
            "page_number": page["page_number"],
            "error": page["image_inspection_error"],
        }
        for page in book["pages"]
        if page["image_inspection_error"]
    ]
    metadata_path.write_text(json.dumps(book, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return book


def build_report(books: list[dict[str, Any]], books_dir: Path, extracted_dir: Path) -> dict[str, Any]:
    duplicate_pages: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for book in books:
        for page in book.get("pages", []):
            page_hash = page.get("duplicate_sha256")
            if page_hash:
                duplicate_pages[page_hash].append(
                    {"book": book["book"], "page_number": page["page_number"]}
                )

    duplicate_groups = [
        locations for locations in duplicate_pages.values() if len(locations) > 1
    ]
    totals = Counter()
    for book in books:
        totals["pages"] += book.get("page_count", 0)
        totals["characters"] += book.get("counts", {}).get("characters", 0)
        totals["quality_text_characters"] += book.get("quality_text_characters", 0)
        totals["words"] += book.get("counts", {}).get("words", 0)
        totals["whitespace_tokens_estimate"] += book.get("counts", {}).get(
            "whitespace_tokens_estimate", 0
        )
        totals["empty_pages"] += len(book.get("empty_page_numbers", []))
        totals["ocr_candidate_pages"] += len(book.get("ocr_candidate_page_numbers", []))
        totals["unreadable_pages"] += len(book.get("unreadable_pages", []))
        totals["image_inspection_errors"] += len(book.get("image_inspection_errors", []))
        totals["encoding_suspect_pages"] += len(book.get("encoding_suspect_page_numbers", []))
        totals["parser_warning_books"] += bool(book.get("parser_warnings"))

    return {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "books_directory": str(books_dir),
        "extracted_text_directory": str(extracted_dir),
        "pdf_count": len(books),
        "totals": dict(totals),
        "duplicate_page_groups": duplicate_groups,
        "notes": [
            "PDF originals were opened read-only and were not modified.",
            "Extracted text is raw pypdf page text with page markers; no spelling correction, translation, or cleanup was applied.",
            "OCR candidates are pages with little substantive extracted text despite expected Assamese content, low text with embedded images, or suspicious encoding indicators. These are candidates for OCR or visual review, not confirmed OCR requirements.",
            "Empty-extraction pages have no substantive text and no detected embedded images. This does not prove that the visual PDF page is blank; vector-only/scanned content may not be identifiable.",
            "Whitespace token counts are estimates, not model-tokenizer counts. The model tokenizer was not downloaded.",
            "Duplicate detection hashes substantive page text after removing matching standalone SCERT copyright/republication notice lines, whitespace normalization, and case folding; source text is retained regardless.",
            "Assamese-script presence is used only as a font-encoding quality signal for files whose names identify Assamese content. It does not distinguish Assamese from Bengali, which share Unicode script ranges.",
            "For quality checks only, matching standalone SCERT copyright/republication notice lines are excluded from the duplicate fingerprint and substantive-text count; they remain intact in extracted output.",
        ],
        "books": books,
    }


def render_markdown(report: dict[str, Any]) -> str:
    totals = report["totals"]
    lines = [
        "# Assamese Textbook PDF Extraction Report",
        "",
        f"- Generated: {report['created_at']}",
        f"- Source directory: `{report['books_directory']}`",
        f"- Extracted output: `{report['extracted_text_directory']}`",
        "- Original PDFs modified: **No**",
        "- Text cleaning/training data preparation: **Not performed (Phase 2 extraction only)**",
        "",
        "## Dataset totals",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| PDFs | {report['pdf_count']} |",
        f"| Pages | {totals.get('pages', 0)} |",
        f"| Extracted characters | {totals.get('characters', 0)} |",
        f"| Substantive characters (copyright notices excluded for this metric only) | {totals.get('quality_text_characters', 0)} |",
        f"| Whitespace-delimited words | {totals.get('words', 0)} |",
        f"| Whitespace-token estimate (not model tokens) | {totals.get('whitespace_tokens_estimate', 0)} |",
        f"| OCR/visual-review candidate pages | {totals.get('ocr_candidate_pages', 0)} |",
        f"| Empty-extraction pages (not confirmed visually blank) | {totals.get('empty_pages', 0)} |",
        f"| Unreadable pages | {totals.get('unreadable_pages', 0)} |",
        f"| Encoding-suspect pages | {totals.get('encoding_suspect_pages', 0)} |",
        f"| Books with parser warnings | {totals.get('parser_warning_books', 0)} |",
        f"| Image-inspection errors | {totals.get('image_inspection_errors', 0)} |",
        f"| Duplicate page-content groups | {len(report['duplicate_page_groups'])} |",
        "",
        "## Per-book results",
        "",
        "| Book | Pages | Characters | Substantive chars | Words | OCR/visual-review candidates | Encoding suspect | Empty extraction | Unreadable | Errors |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for book in report["books"]:
        counts = book.get("counts", {})
        safe_book_name = book["book"].replace("|", "\\|")
        lines.append(
            f"| {safe_book_name} | {book.get('page_count', 0)} "
            f"| {counts.get('characters', 0)} | {book.get('quality_text_characters', 0)} "
            f"| {counts.get('words', 0)} "
            f"| {len(book.get('ocr_candidate_page_numbers', []))} "
            f"| {len(book.get('encoding_suspect_page_numbers', []))} "
            f"| {len(book.get('empty_page_numbers', []))} "
            f"| {len(book.get('unreadable_pages', []))} "
            f"| {len(book.get('book_errors', []))} |"
        )
    lines.extend(["", "## OCR/visual-review candidates and extraction errors", ""])
    any_details = False
    for book in report["books"]:
        if (
            book.get("ocr_candidate_page_numbers")
            or book.get("unreadable_pages")
            or book.get("book_errors")
            or book.get("image_inspection_errors")
            or book.get("parser_warnings")
        ):
            any_details = True
            lines.append(f"### {book['book']}")
            lines.append("")
            if book.get("ocr_candidate_page_numbers"):
                lines.append(
                    "OCR candidate pages (1-based): "
                    + ", ".join(map(str, book["ocr_candidate_page_numbers"]))
                )
                lines.append("")
            for error in book.get("book_errors", []):
                lines.append(f"- Book error: {error}")
            for page in book.get("unreadable_pages", []):
                lines.append(f"- Page {page['page_number']} error: {page['error']}")
            for page in book.get("image_inspection_errors", []):
                lines.append(
                    f"- Page {page['page_number']} image-inspection error: {page['error']}"
                )
            if book.get("encoding_suspect_page_numbers"):
                lines.append(
                    "Encoding-suspect pages (1-based): "
                    + ", ".join(map(str, book["encoding_suspect_page_numbers"]))
                )
                lines.append("")
            for parser_warning in book.get("parser_warnings", []):
                lines.append(f"- Parser warning: {parser_warning}")
            lines.append("")
    if not any_details:
        lines.extend(["No OCR candidates or extraction errors were detected.", ""])

    lines.extend(["## Duplicate page text", ""])
    if report["duplicate_page_groups"]:
        for group in report["duplicate_page_groups"]:
            formatted = ", ".join(f"{item['book']} p.{item['page_number']}" for item in group)
            lines.append(f"- {formatted}")
    else:
        lines.append("No exact duplicate page text found after whitespace normalization and case folding.")
    lines.extend(["", "## Method and limitations", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.extend(
        [
            "- OCR tools are not installed in the current environment. Assamese OCR support was investigated separately; OCR candidates are reported, not processed.",
            "- OCR candidate pages may still contain useful extracted text; inspect both the PDF and extracted output before replacing or combining text.",
            "- Some PDFs visibly contain a SCERT Assam notice stating that they are not to be republished. Do not use these books for training or redistribute their extracted text without checking rights and obtaining required permission.",
            "- This report describes extraction outcomes only. It does not imply the extracted corpus is cleaned, licensed for model training, deduplicated, or ready to train.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract page text and report PDF quality without editing source books.")
    parser.add_argument("--books-dir", type=Path, default=DEFAULT_BOOKS_DIR)
    parser.add_argument("--extracted-dir", type=Path, default=DEFAULT_EXTRACTED_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    args = parser.parse_args()

    for directory in REQUIRED_DIRECTORIES:
        directory.mkdir(parents=True, exist_ok=True)
    args.extracted_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    if not args.books_dir.is_dir():
        parser.error(f"PDF books directory does not exist: {args.books_dir}")
    pdf_paths = sorted(args.books_dir.rglob("*.pdf"), key=lambda path: path.as_posix().casefold())
    books = []
    for index, pdf_path in enumerate(pdf_paths, start=1):
        print(f"[{index}/{len(pdf_paths)}] Extracting {pdf_path.name}", flush=True)
        books.append(_extract_book(pdf_path, args.books_dir, args.extracted_dir))

    report = build_report(books, args.books_dir, args.extracted_dir)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    json_path = args.reports_dir / f"textbook-extraction-{timestamp}.json"
    markdown_path = args.reports_dir / f"textbook-extraction-{timestamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    print(f"\nREPORT={markdown_path}")
    print(f"DETAILS={json_path}")
    print(
        "TOTALS "
        + json.dumps(
            {
                "pdf_count": report["pdf_count"],
                **report["totals"],
                "duplicate_page_groups": len(report["duplicate_page_groups"]),
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["totals"].get("unreadable_pages", 0) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
