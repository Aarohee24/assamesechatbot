from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from typing import Any

import pypdfium2 as pdfium


PROJECT_ROOT = Path(__file__).resolve().parents[1]
BOOKS_DIR = PROJECT_ROOT / "data" / "books"
REPORTS_DIR = PROJECT_ROOT / "reports"
TESSERACT_CANDIDATES = (
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
)
RENDER_DPI = 300
PAGE_SEGMENTATION_MODES = (3, 6, 11)
SAMPLE_PAGES = (
    ("Ami Aru Amar Paribesh_Class V_Assamese.pdf", 6, "interior image page with footer-only native text"),
    ("Ankuran (Pancham Bhag) (Language (L1))_Class 5_Assamese medium.pdf", 6, "interior image page with footer-only native text"),
    ("Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf", 7, "interior page with suspicious font mapping"),
    ("Ankuran (Sastha Bhag) (Language (L1))_Class 6_Assamese medium.pdf", 6, "interior image page with footer-only native text"),
    ("Assamese.pdf", 7, "scanned text page with no extracted text"),
    ("Bigyan (C) (With keywords in English) (Science)_Class 7_Assamese medium.pdf", 6, "interior page with suspicious font mapping"),
    ("Bigyan_VIII_Part-II_Assamese.pdf", 20, "interior science page; verify whether it contains Assamese"),
    ("Dwiniyat (Old) (R)(Dwiniyat)_Class 7_Assamese medium.pdf", 6, "interior image page with footer-only native text"),
    ("Sahitya Karani (Pratham Bhag) (L3 (Assamese))_Class 6.pdf", 6, "interior image page with footer-only native text"),
    ("Sahitya Karani (Tritiya Bhag) (L3 (Assamese))_Class 8.pdf", 7, "interior page with suspicious font mapping"),
    ("Samaj Bichitra_Class VI_Textbook_Assamese.pdf", 24, "interior page with suspicious font mapping"),
    ("Samaj Bigyan (Dwitiya Bhag) (Social Science)_Class 7_Assamese medium.pdf", 6, "interior image page with footer-only native text"),
    ("Science_Class VI_Part 1_Assamese.pdf", 250, "interior page with suspicious font mapping and images"),
    ("Spandan-Part I-ClassIII-Assamese(L1).pdf", 6, "interior image page with footer-only native text"),
    ("Unmesh I-Class VI-Assamese.pdf", 7, "interior page with suspicious font mapping and images"),
)


def _find_tesseract(explicit_path: Path | None) -> Path:
    if explicit_path is not None:
        if not explicit_path.is_file():
            raise FileNotFoundError(f"Tesseract executable not found: {explicit_path}")
        return explicit_path
    on_path = shutil.which("tesseract")
    if on_path:
        return Path(on_path)
    for candidate in TESSERACT_CANDIDATES:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        "Tesseract was not found. Install it or pass --tesseract-path."
    )


def _assamese_stats(text: str) -> dict[str, int | float]:
    letters = [character for character in text if character.isalpha()]
    assamese_letters = [
        character
        for character in letters
        if "\u0980" <= character <= "\u09ff"
    ]
    return {
        "characters": len(text),
        "alphabetic_characters": len(letters),
        "assamese_block_letters": len(assamese_letters),
        "assamese_block_letter_ratio": (
            round(len(assamese_letters) / len(letters), 4) if letters else 0.0
        ),
        "whitespace_words": len(text.split()),
        "replacement_characters": text.count("\ufffd"),
    }


def _page_raw_text(extraction_report: dict[str, Any], book_name: str, page_number: int) -> str:
    for book in extraction_report.get("books", []):
        if book["book"] == book_name:
            pages = book.get("pages", [])
            if page_number <= len(pages):
                return pages[page_number - 1].get("text", "")
            break
    return ""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_tesseract(
    executable: Path,
    image_path: Path,
    *,
    psm: int,
    timeout_seconds: int,
) -> tuple[str, str, float]:
    command = [
        str(executable),
        str(image_path),
        "stdout",
        "-l",
        "asm",
        "--oem",
        "1",
        "--psm",
        str(psm),
        "--dpi",
        str(RENDER_DPI),
        "-c",
        "preserve_interword_spaces=1",
    ]
    started_at = time.perf_counter()
    result = subprocess.run(
        command,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        timeout=timeout_seconds,
    )
    if result.returncode:
        raise RuntimeError(
            f"Tesseract failed for {image_path.name}, PSM {psm}: "
            f"{result.stderr.strip() or f'exit code {result.returncode}'}"
        )
    elapsed_seconds = time.perf_counter() - started_at
    return result.stdout.strip(), result.stderr.strip(), elapsed_seconds


def _evaluate_sample(
    *,
    book_path: Path,
    page_number: int,
    rationale: str,
    extraction_report: dict[str, Any],
    executable: Path,
    output_dir: Path,
    timeout_seconds: int,
) -> dict[str, Any]:
    document = pdfium.PdfDocument(str(book_path))
    try:
        if page_number < 1 or page_number > len(document):
            raise ValueError(f"{book_path.name} has no page {page_number}")
        page = document[page_number - 1]
        bitmap = page.render(scale=RENDER_DPI / 72)
        try:
            image_path = output_dir / f"{book_path.stem}-page-{page_number}.png"
            bitmap.to_pil().save(image_path, format="PNG")
        finally:
            bitmap.close()
    finally:
        document.close()

    raw_text = _page_raw_text(extraction_report, book_path.name, page_number)
    methods = []
    for psm in PAGE_SEGMENTATION_MODES:
        text, stderr, elapsed_seconds = _run_tesseract(
            executable,
            image_path,
            psm=psm,
            timeout_seconds=timeout_seconds,
        )
        methods.append(
            {
                "engine": "Tesseract LSTM",
                "language": "asm",
                "oem": 1,
                "psm": psm,
                "dpi": RENDER_DPI,
                "text": text,
                "stats": _assamese_stats(text),
                "elapsed_seconds": round(elapsed_seconds, 3),
                "stderr": stderr,
                "human_review": "Required; Unicode/script counts do not measure correctness.",
            }
        )

    return {
        "book": book_path.name,
        "page_number": page_number,
        "sample_reason": rationale,
        "render_dpi": RENDER_DPI,
        "image_width": bitmap.width,
        "image_height": bitmap.height,
        "page_image": image_path.name,
        "page_image_sha256": _sha256(image_path),
        "native_text": raw_text,
        "native_text_stats": _assamese_stats(raw_text),
        "ocr_methods": methods,
        "visual_review": "Rendered page saved for side-by-side human review.",
    }


def _render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Assamese OCR Sample Evaluation",
        "",
        f"- Generated: {report['created_at']}",
        f"- Tesseract: `{report['tesseract_version']}`",
        f"- Installed languages: `{', '.join(report['installed_languages'])}`",
        f"- Renderer: pypdfium2",
        f"- Rendering: {report['render_dpi']} DPI",
        f"- OCR: Tesseract LSTM (`--oem 1`, language `asm`), page segmentation modes "
        + ", ".join(map(str, report["page_segmentation_modes"])),
        f"- Scope: {len(report['samples'])} selected sample pages only; no full-book OCR or extracted-text replacement.",
        "- Original PDFs and existing raw extraction files were not modified.",
        "",
        "## Results",
        "",
        "| PDF page | Sample reason | Native Assamese-block letters | OCR PSM 3 | OCR PSM 6 | OCR PSM 11 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for sample in report["samples"]:
        counts = {
            method["psm"]: method["stats"]["assamese_block_letters"]
            for method in sample["ocr_methods"]
        }
        lines.append(
            f"| `{sample['book']}` p.{sample['page_number']} "
            f"| {sample['sample_reason']} "
            f"| {sample['native_text_stats']['assamese_block_letters']} "
            f"| {counts[3]} | {counts[6]} | {counts[11]} |"
        )

    lines.extend(["", "## Per-page comparison", ""])
    for sample in report["samples"]:
        lines.extend(
            [
                f"### {sample['book']} — page {sample['page_number']}",
                "",
                f"- Sample rationale: {sample['sample_reason']}",
                f"- Original rendered page: `{sample['page_image']}` "
                f"({sample['image_width']} × {sample['image_height']}, "
                f"SHA-256 `{sample['page_image_sha256']}`)",
                f"- Native extraction metrics: `{json.dumps(sample['native_text_stats'], ensure_ascii=True)}`",
                "- Visual comparison status: OCR text requires manual reading against the saved page image. "
                "Character/script metrics alone are not an accuracy measure.",
                "",
                "#### Existing raw extracted text (unchanged)",
                "",
                "```text",
                sample["native_text"] or "[No text extracted]",
                "```",
            ]
        )
        for method in sample["ocr_methods"]:
            lines.extend(
                [
                    f"#### Tesseract PSM {method['psm']}",
                    "",
                    f"- Settings: language `{method['language']}`, OEM {method['oem']}, "
                    f"PSM {method['psm']}, {method['dpi']} DPI",
                    f"- Metrics: `{json.dumps(method['stats'], ensure_ascii=True)}`",
                    f"- OCR elapsed time: {method['elapsed_seconds']} seconds",
                    "",
                    "```text",
                    method["text"] or "[No text recognized]",
                    "```",
                    "",
                ]
            )
    lines.extend(
        [
            "## Limitations and review",
            "",
            "- Assam and Bengali share the Unicode block measured here. An Assamese-block count does not prove that the OCR language is Assamese, nor that the text is readable or faithful.",
            "- Tesseract has only the `asm` language pack installed; English/Bengali packs were not used or fetched.",
            "- Inspect the saved PNG alongside each exact OCR output. Mark page transcription quality manually before using any OCR result.",
            "- OCR output is diagnostic only. This report does not clean, merge, or replace raw extracted text.",
            "- The sample is diagnostic, not representative proof for every page or every PDF. Review rights before any future training use.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OCR only a fixed small sample of textbook pages for human review."
    )
    parser.add_argument("--tesseract-path", type=Path)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    args = parser.parse_args()
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")

    executable = _find_tesseract(args.tesseract_path)
    version = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
    ).stdout.splitlines()[0]
    languages_result = subprocess.run(
        [str(executable), "--list-langs"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
    )
    installed_languages = [
        line.strip()
        for line in languages_result.stdout.splitlines()[1:]
        if line.strip()
    ]
    if "asm" not in installed_languages:
        raise RuntimeError(
            f"Tesseract Assamese language data ('asm') is unavailable: "
            f"{installed_languages}"
        )

    extraction_reports = sorted(
        REPORTS_DIR.glob("textbook-extraction-*.json"), reverse=True
    )
    if not extraction_reports:
        raise FileNotFoundError("No textbook extraction JSON report found.")
    extraction_report_path = extraction_reports[0]
    extraction_report = json.loads(
        extraction_report_path.read_text(encoding="utf-8")
    )

    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    output_dir = REPORTS_DIR / f"ocr-sample-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=False)
    samples = []
    for book_name, page_number, rationale in SAMPLE_PAGES:
        book_path = BOOKS_DIR / book_name
        if not book_path.is_file():
            raise FileNotFoundError(f"Sample PDF not found: {book_path}")
        samples.append(
            _evaluate_sample(
                book_path=book_path,
                page_number=page_number,
                rationale=rationale,
                extraction_report=extraction_report,
                executable=executable,
                output_dir=output_dir,
                timeout_seconds=args.timeout_seconds,
            )
        )

    report = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "tesseract_path": str(executable),
        "tesseract_version": version,
        "installed_languages": installed_languages,
        "renderer": "pypdfium2",
        "render_dpi": RENDER_DPI,
        "page_segmentation_modes": PAGE_SEGMENTATION_MODES,
        "source_extraction_report": str(extraction_report_path),
        "sample_scope": "fixed sample only; never processes all PDF pages",
        "samples": samples,
    }
    json_path = REPORTS_DIR / f"assamese-ocr-sample-{timestamp}.json"
    markdown_path = REPORTS_DIR / f"assamese-ocr-sample-{timestamp}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    markdown_path.write_text(_render_markdown(report), encoding="utf-8")
    print(f"REPORT={markdown_path}")
    print(f"DETAILS={json_path}")
    print(f"PAGE_IMAGES={output_dir}")
    print(
        f"SAMPLES={len(samples)} "
        f"OCR_RUNS={len(samples) * len(PAGE_SEGMENTATION_MODES)}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
