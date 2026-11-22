from __future__ import annotations

import argparse
import csv
from datetime import datetime
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from typing import Any
from urllib.parse import quote

import psutil
import pypdfium2 as pdfium


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BOOKS_DIR = PROJECT_ROOT / "data" / "books"
DEFAULT_OCR_DIR = PROJECT_ROOT / "data" / "ocr_text"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"
TESSERACT_CANDIDATES = (
    Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
    Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
)
RENDER_DPI = 300
OCR_LANGUAGE = "asm"
OCR_OEM = 1
OCR_PSM = 3
LOW_CONFIDENCE_THRESHOLD = 60.0
DEFAULT_PILOT_PAGE_COUNT = 50
DEFAULT_MAX_ATTEMPTS = 2
DEFAULT_TIMEOUT_SECONDS = 120
POLL_INTERVAL_SECONDS = 0.1
INDICLID_REPOSITORY = "ai4bharat/IndicLID-FTN"
INDICLID_REVISION = "68c6f11c13174d7f2e734012f2d1cad4449254ae"
INDICLID_MODEL_FILE = "model_baseline_roman.bin"
LANGUAGE_REVIEW_THRESHOLD = 0.75


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


def _tesseract_info(executable: Path) -> tuple[str, list[str]]:
    version_result = subprocess.run(
        [str(executable), "--version"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    languages_result = subprocess.run(
        [str(executable), "--list-langs"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    version_lines = version_result.stdout.splitlines()
    if not version_lines:
        raise RuntimeError("Tesseract returned no version information.")
    languages = [
        line.strip()
        for line in languages_result.stdout.splitlines()[1:]
        if line.strip()
    ]
    if OCR_LANGUAGE not in languages:
        raise RuntimeError(
            f"Tesseract Assamese language data ('{OCR_LANGUAGE}') is unavailable: "
            f"{languages}"
        )
    return version_lines[0], languages


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_stem(path: Path) -> str:
    return re.sub(r'[<>:"/\\|?*]+', "_", path.stem).strip(" .") or "book"


def _relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def _atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary_path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _record_is_reusable(
    record: dict[str, Any] | None,
    *,
    source_sha256: str,
    settings_id: str,
) -> bool:
    return bool(
        record
        and record.get("status") == "completed"
        and record.get("source_pdf_sha256") == source_sha256
        and record.get("settings_id") == settings_id
    )


def _inventory_books(book_paths: list[Path]) -> list[dict[str, Any]]:
    inventory = []
    for book_path in book_paths:
        item: dict[str, Any] = {
            "book": book_path.name,
            "source_relative_path": _relative_path(book_path),
            "source_pdf_size_bytes": book_path.stat().st_size,
            "source_pdf_sha256": _sha256(book_path),
            "page_count": None,
            "pdf_metadata": {},
            "metadata_error": None,
            "inventory_error": None,
        }
        document = None
        try:
            document = pdfium.PdfDocument(str(book_path))
            item["page_count"] = len(document)
            try:
                metadata = document.get_metadata_dict()
                item["pdf_metadata"] = {
                    str(key): str(value) if value is not None else None
                    for key, value in (metadata or {}).items()
                }
            except Exception as error:
                item["metadata_error"] = f"{type(error).__name__}: {error}"
        except Exception as error:
            item["inventory_error"] = f"{type(error).__name__}: {error}"
        finally:
            if document is not None:
                document.close()
        inventory.append(item)
    return inventory


def _select_pilot_pages(
    inventory: list[dict[str, Any]], target_count: int
) -> list[tuple[int, int]]:
    available = [
        (book_index, int(book["page_count"]))
        for book_index, book in enumerate(inventory)
        if book["page_count"] is not None and int(book["page_count"]) > 0
    ]
    total_available = sum(page_count for _, page_count in available)
    target_count = min(target_count, total_available)
    allocations = {book_index: 0 for book_index, _ in available}
    remaining = target_count
    while remaining:
        made_progress = False
        for book_index, page_count in available:
            if allocations[book_index] < page_count and remaining:
                allocations[book_index] += 1
                remaining -= 1
                made_progress = True
        if not made_progress:
            break

    selected = []
    for book_index, page_count in available:
        count = allocations[book_index]
        chosen: set[int] = set()
        for index in range(count):
            page_number = int(round((index + 1) * (page_count + 1) / (count + 1)))
            chosen.add(max(1, min(page_count, page_number)))
        if len(chosen) < count:
            for page_number in range(1, page_count + 1):
                chosen.add(page_number)
                if len(chosen) == count:
                    break
        selected.extend((book_index, page_number) for page_number in sorted(chosen))
    return selected


def _parse_tsv_confidence(tsv_text: str) -> dict[str, float | int | None]:
    scores = []
    try:
        rows = csv.DictReader(io.StringIO(tsv_text), delimiter="\t")
        for row in rows:
            if row.get("level") != "5" or not (row.get("text") or "").strip():
                continue
            try:
                score = float(row["conf"])
            except (KeyError, TypeError, ValueError):
                continue
            if score >= 0:
                scores.append(score)
    except csv.Error:
        scores = []
    if not scores:
        return {
            "word_count": 0,
            "mean": None,
            "median": None,
            "minimum": None,
            "maximum": None,
        }
    return {
        "word_count": len(scores),
        "mean": round(sum(scores) / len(scores), 2),
        "median": round(float(statistics.median(scores)), 2),
        "minimum": round(min(scores), 2),
        "maximum": round(max(scores), 2),
    }


def _load_cached_language_model(logger: logging.Logger) -> tuple[Any | None, dict[str, Any]]:
    try:
        from huggingface_hub import try_to_load_from_cache

        model_path = try_to_load_from_cache(
            INDICLID_REPOSITORY,
            INDICLID_MODEL_FILE,
            revision=INDICLID_REVISION,
        )
        if not model_path:
            message = (
                "Pinned IndicLID model is not present in the local Hugging Face cache; "
                "network downloads are disabled."
            )
            logger.warning(message)
            return None, {
                "available": False,
                "repository": INDICLID_REPOSITORY,
                "revision": INDICLID_REVISION,
                "error": message,
            }
        import fasttext

        model = fasttext.load_model(str(model_path))
        return model, {
            "available": True,
            "repository": INDICLID_REPOSITORY,
            "revision": INDICLID_REVISION,
            "source": "existing local Hugging Face cache; no network access",
            "confidence_threshold_for_uncertain_flag": LANGUAGE_REVIEW_THRESHOLD,
        }
    except (ImportError, OSError, RuntimeError, ValueError, EOFError) as error:
        message = f"{type(error).__name__}: {error}"
        logger.warning("Local IndicLID model could not be loaded: %s", message)
        return None, {
            "available": False,
            "repository": INDICLID_REPOSITORY,
            "revision": INDICLID_REVISION,
            "error": message,
        }


def _classify_page_language(model: Any | None, text: str) -> dict[str, Any]:
    if model is None:
        return {"status": "unavailable", "label": None, "confidence": None, "error": None}
    if not text.strip():
        return {"status": "empty", "label": None, "confidence": None, "error": None}
    try:
        labels, scores = model.predict(" ".join(text.splitlines()), k=2)
        if len(labels) == 0 or len(scores) == 0:
            raise ValueError("IndicLID returned no language prediction.")
        label = str(labels[0]).removeprefix("__label__")
        return {
            "status": "classified",
            "label": label,
            "confidence": round(float(scores[0]), 4),
            "error": None,
        }
    except Exception as error:
        return {
            "status": "error",
            "label": None,
            "confidence": None,
            "error": f"{type(error).__name__}: {error}",
        }


def _review_flags(
    text: str,
    confidence: dict[str, Any],
    language: dict[str, Any] | None = None,
) -> list[str]:
    flags = []
    if not text.strip():
        flags.append("empty_ocr")
    mean_confidence = confidence.get("mean")
    if mean_confidence is not None and mean_confidence < LOW_CONFIDENCE_THRESHOLD:
        flags.append("low_confidence")
    alpha = [character for character in text if character.isalpha()]
    assamese_block = [
        character for character in alpha if "\u0980" <= character <= "\u09ff"
    ]
    latin = [
        character
        for character in alpha
        if "A" <= character <= "Z" or "a" <= character <= "z"
    ]
    english_candidate = (
        len(alpha) >= 20
        and not assamese_block
        and len(latin) / len(alpha) >= 0.85
    )
    language_label = (language or {}).get("label")
    language_confidence = (language or {}).get("confidence")
    if language_label == "eng_Latn":
        english_candidate = True
    if english_candidate:
        flags.append("english_only_candidate")
    if language_label == "ben_Beng":
        flags.append("bengali_or_non_assamese_candidate")
    if (
        language_label
        and language_label != "asm_Beng"
        and language_confidence is not None
        and language_confidence < LANGUAGE_REVIEW_THRESHOLD
    ):
        flags.append("language_uncertain")
    if (language or {}).get("status") in {"unavailable", "error"}:
        flags.append("language_check_unavailable")
    if text.strip() and not assamese_block:
        flags.append("no_assamese_block_text_candidate")
    if (
        "\ufffd" in text
        or any(ord(char) < 32 and char not in "\r\n\t" for char in text)
        or (alpha and not assamese_block and not english_candidate)
    ):
        flags.append("suspicious_text")
    flags.append("human_review_required")
    return flags


def _current_process_tree_rss(process: psutil.Process) -> int:
    rss = 0
    processes = [process]
    try:
        processes.extend(process.children(recursive=True))
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    for child in processes:
        try:
            rss += child.memory_info().rss
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return rss


def _run_tesseract(
    executable: Path,
    image_path: Path,
    *,
    output_format: str,
    timeout_seconds: int,
) -> tuple[str, str, float, int]:
    command = [
        str(executable),
        str(image_path),
        "stdout",
        "-l",
        OCR_LANGUAGE,
        "--oem",
        str(OCR_OEM),
        "--psm",
        str(OCR_PSM),
        "--dpi",
        str(RENDER_DPI),
        "-c",
        "preserve_interword_spaces=1",
    ]
    if output_format == "tsv":
        command.append("tsv")
    elif output_format != "txt":
        raise ValueError(f"Unsupported Tesseract output format: {output_format}")

    parent = psutil.Process(os.getpid())
    started_at = time.perf_counter()
    child = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
        errors="replace",
    )
    peak_rss = _current_process_tree_rss(parent)
    try:
        try:
            while True:
                try:
                    stdout, stderr = child.communicate(
                        timeout=POLL_INTERVAL_SECONDS
                    )
                    break
                except subprocess.TimeoutExpired:
                    peak_rss = max(peak_rss, _current_process_tree_rss(parent))
                    if time.perf_counter() - started_at > timeout_seconds:
                        child.kill()
                        stdout, stderr = child.communicate()
                        raise subprocess.TimeoutExpired(
                            command,
                            timeout_seconds,
                            output=stdout,
                            stderr=stderr,
                        )
        finally:
            if child.poll() is None:
                child.kill()
                child.communicate()
    finally:
        peak_rss = max(peak_rss, _current_process_tree_rss(parent))
    elapsed_seconds = time.perf_counter() - started_at
    if child.returncode:
        raise RuntimeError(
            f"Tesseract {output_format} failed for {image_path.name}: "
            f"{stderr.strip() or f'exit code {child.returncode}'}"
        )
    return stdout, stderr.strip(), elapsed_seconds, peak_rss


def _render_page_image(
    document: Any,
    page_number: int,
    image_path: Path,
) -> tuple[int, int]:
    page = document[page_number - 1]
    bitmap = page.render(scale=RENDER_DPI / 72)
    try:
        pil_image = bitmap.to_pil()
        try:
            image_path.parent.mkdir(parents=True, exist_ok=True)
            pil_image.save(image_path, format="PNG")
            return int(bitmap.width), int(bitmap.height)
        finally:
            pil_image.close()
    finally:
        bitmap.close()


def _page_record_path(
    ocr_dir: Path,
    settings_id: str,
    book: dict[str, Any],
    page_number: int,
) -> Path:
    book_id = f"{_safe_stem(Path(book['book']))}_{book['source_pdf_sha256'][:12]}"
    return (
        ocr_dir
        / "runs"
        / settings_id
        / "pages"
        / book_id
        / f"page-{page_number:06d}.json"
    )


def _process_page(
    *,
    document: Any,
    book: dict[str, Any],
    page_number: int,
    settings_id: str,
    image_path: Path | None,
    tesseract_path: Path,
    timeout_seconds: int,
    max_attempts: int,
    logger: logging.Logger,
    language_model: Any | None,
) -> dict[str, Any]:
    errors = []
    attempt_records = []
    for attempt_number in range(1, max_attempts + 1):
        temporary_image_path: Path | None = None
        page_started = time.perf_counter()
        try:
            if image_path is None:
                with tempfile.NamedTemporaryFile(
                    prefix="assamese-ocr-", suffix=".png", delete=False
                ) as temporary_image:
                    temporary_image_path = Path(temporary_image.name)
                target_image = temporary_image_path
            else:
                target_image = image_path
            width, height = _render_page_image(document, page_number, target_image)
            text, text_stderr, text_seconds, text_peak_rss = _run_tesseract(
                tesseract_path,
                target_image,
                output_format="txt",
                timeout_seconds=timeout_seconds,
            )
            tsv, tsv_stderr, tsv_seconds, tsv_peak_rss = _run_tesseract(
                tesseract_path,
                target_image,
                output_format="tsv",
                timeout_seconds=timeout_seconds,
            )
            text = text.strip()
            confidence = _parse_tsv_confidence(tsv)
            language = _classify_page_language(language_model, text)
            if language["status"] == "error":
                logger.warning(
                    "Page language check failed: %s p.%s: %s",
                    book["book"],
                    page_number,
                    language["error"],
                )
            flags = _review_flags(text, confidence, language)
            stderr = [message for message in (text_stderr, tsv_stderr) if message]
            attempt_records.append(
                {
                    "attempt": attempt_number,
                    "result": "completed",
                    "tesseract_warnings": stderr,
                }
            )
            record = {
                **book,
                "page_number": page_number,
                "status": "completed",
                "settings_id": settings_id,
                "render_dpi": RENDER_DPI,
                "language": OCR_LANGUAGE,
                "oem": OCR_OEM,
                "psm": OCR_PSM,
                "text": text,
                "confidence": confidence,
                "language_identification": language,
                "review_flags": flags,
                "attempt_count": attempt_number,
                "attempts": attempt_records,
                "errors": errors,
                "page_image": _relative_path(image_path) if image_path else None,
                "page_image_sha256": _sha256(image_path) if image_path else None,
                "image_width": width,
                "image_height": height,
                "ocr_elapsed_seconds": round(text_seconds + tsv_seconds, 3),
                "page_elapsed_seconds": round(time.perf_counter() - page_started, 3),
                "peak_process_tree_rss_bytes": max(text_peak_rss, tsv_peak_rss),
                "tesseract_warnings": stderr,
            }
            return record
        except Exception as error:
            error_message = f"{type(error).__name__}: {error}"
            errors.append(error_message)
            attempt_records.append(
                {
                    "attempt": attempt_number,
                    "result": "failed",
                    "error": error_message,
                }
            )
            logger.warning(
                "Page attempt failed: %s p.%s attempt %s/%s: %s",
                book["book"],
                page_number,
                attempt_number,
                max_attempts,
                error_message,
            )
            if attempt_number < max_attempts:
                continue
        finally:
            if temporary_image_path is not None:
                temporary_image_path.unlink(missing_ok=True)

    return {
        **book,
        "page_number": page_number,
        "status": "failed",
        "settings_id": settings_id,
        "render_dpi": RENDER_DPI,
        "language": OCR_LANGUAGE,
        "oem": OCR_OEM,
        "psm": OCR_PSM,
        "text": "",
        "confidence": _parse_tsv_confidence(""),
        "language_identification": _classify_page_language(language_model, ""),
        "review_flags": ["page_processing_failed", "human_review_required"],
        "attempt_count": max_attempts,
        "attempts": attempt_records,
        "errors": errors,
        "page_image": _relative_path(image_path) if image_path and image_path.is_file() else None,
        "page_image_sha256": (
            _sha256(image_path) if image_path and image_path.is_file() else None
        ),
        "ocr_elapsed_seconds": None,
        "page_elapsed_seconds": None,
        "peak_process_tree_rss_bytes": None,
        "tesseract_warnings": [],
    }


def _new_run_directory(reports_dir: Path) -> tuple[str, Path]:
    base = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    for suffix in range(1000):
        run_id = base if suffix == 0 else f"{base}-{suffix:02d}"
        run_dir = reports_dir / f"assamese-ocr-run-{run_id}"
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
            return run_id, run_dir
        except FileExistsError:
            continue
    raise FileExistsError("Could not allocate a unique timestamped OCR report directory.")


def _summarize_book(
    book: dict[str, Any],
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    completed = [record for record in records if record["status"] == "completed"]
    failed = [record for record in records if record["status"] == "failed"]
    confidences = [
        record["confidence"]["mean"]
        for record in completed
        if record["confidence"]["mean"] is not None
    ]
    runtimes = [
        record["page_elapsed_seconds"]
        for record in records
        if record["page_elapsed_seconds"] is not None
    ]
    flag_counts: dict[str, int] = {}
    for record in records:
        for flag in record["review_flags"]:
            flag_counts[flag] = flag_counts.get(flag, 0) + 1
    return {
        **book,
        "selected_page_count": len(records),
        "completed_page_count": len(completed),
        "failed_page_count": len(failed),
        "mean_word_confidence": (
            round(sum(confidences) / len(confidences), 2) if confidences else None
        ),
        "total_page_processing_seconds": round(sum(runtimes), 3),
        "review_flag_counts": flag_counts,
        "failed_pages": [
            {
                "page_number": record["page_number"],
                "errors": record["errors"],
            }
            for record in failed
        ],
    }


def _render_book_markdown(
    summary: dict[str, Any],
    records: list[dict[str, Any]],
    *,
    include_full_text: bool,
) -> str:
    lines = [
        f"# OCR report: {summary['book']}",
        "",
        f"- PDF: `{summary['source_relative_path']}`",
        f"- SHA-256: `{summary['source_pdf_sha256']}`",
        f"- Pages in PDF: {summary['page_count']}",
        f"- PDF metadata: `{json.dumps(summary['pdf_metadata'], ensure_ascii=False)}`",
        f"- Selected pages: {summary['selected_page_count']}",
        f"- Completed: {summary['completed_page_count']}; failed: {summary['failed_page_count']}",
        f"- Mean word confidence (where available): {summary['mean_word_confidence']}",
        f"- OCR processing time: {summary['total_page_processing_seconds']} seconds",
        "",
        "All OCR text is raw output. It has not been corrected or approved for training.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## Page {record['page_number']} — {record['status']}",
                "",
                f"- Confidence: `{json.dumps(record['confidence'], ensure_ascii=False)}`",
                f"- Local language ID: `{json.dumps(record.get('language_identification', {}), ensure_ascii=False)}`",
                f"- Review flags: `{', '.join(record['review_flags'])}`",
                f"- Attempts: {record['attempt_count']}; page time: {record['page_elapsed_seconds']} s; "
                f"OCR time: {record['ocr_elapsed_seconds']} s",
                f"- Peak process-tree RSS: {record['peak_process_tree_rss_bytes']} bytes",
                f"- Page image: `{record['page_image'] or 'not retained'}`",
            ]
        )
        if record["errors"]:
            lines.extend(["- Errors:", *[f"  - {error}" for error in record["errors"]]])
        if record["status"] == "completed":
            text = record["text"]
            if not include_full_text and len(text) > 500:
                text = text[:500] + "\n[truncated in report; full text is in the page JSON]"
            lines.extend(["", "```text", text or "[No text recognized]", "```", ""])
        else:
            lines.extend(["", "OCR failed after retry attempts; inspect the page image and error log.", ""])
    return "\n".join(lines)


def _render_overall_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Assamese Textbook OCR Run",
        "",
        f"- Generated: {report['created_at']}",
        f"- Scope: {report['scope']}",
        f"- PDFs discovered: {report['pdf_count']}",
        f"- Total pages inventoried: {report['total_pages']}",
        f"- Pages selected for this run: {report['selected_page_count']}",
        f"- Pages newly processed: {report['newly_processed_page_count']}",
        f"- Previously completed pages reused: {report['reused_page_count']}",
        f"- Failed selected pages: {report['failed_page_count']}",
        f"- Pages not included in this pilot: {report['not_selected_page_count']}",
        f"- Sum of page OCR processing times (including reused pages): {report['page_ocr_total_elapsed_seconds']} seconds",
        f"- This invocation elapsed time (includes inventory/reporting and cached language checks): {report['run_elapsed_seconds']} seconds",
        f"- Peak RSS during page OCR: {report['peak_page_ocr_process_tree_rss_bytes']} bytes",
        f"- Peak RSS including local classifier loading/checks: {report['peak_process_tree_rss_bytes']} bytes",
        f"- RSS after classifier load: {report['language_inference_rss_bytes']} bytes",
        f"- Memory measurement: {report['memory_measurement_note']}",
        f"- Tesseract: `{report['tesseract_version']}`; languages: "
        f"`{', '.join(report['installed_languages'])}`",
        f"- Local language classifier available: {report['language_classifier']['available']} "
        f"(cache-only; no model download)",
        f"- OCR settings: pypdfium2 at {RENDER_DPI} DPI; Tesseract `{OCR_LANGUAGE}`, "
        f"OEM {OCR_OEM}, PSM {OCR_PSM}; timeout {report['timeout_seconds']} s; "
        f"maximum attempts {report['max_attempts']}",
        "- OCR output is saved separately under `data/ocr_text/`; original PDFs and raw extraction outputs are not changed.",
        "- Every OCR page is flagged for human review; confidence and language/script heuristics are not proof of correctness.",
        "",
        "## Per-book summary",
        "",
        "| PDF | Pages in book | Selected | Completed | Failed | Mean confidence | Review flags | Report |",
        "|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for book in report["books"]:
        summary = book["summary"]
        per_book_report = book.get("report_path")
        report_link = (
            f"[open]({quote(per_book_report, safe='/._-')})"
            if per_book_report
            else "not generated"
        )
        flags = ", ".join(
            f"{key}: {value}"
            for key, value in sorted(summary["review_flag_counts"].items())
        )
        lines.append(
            f"| {summary['book']} | {summary['page_count']} | "
            f"{summary['selected_page_count']} | {summary['completed_page_count']} | "
            f"{summary['failed_page_count']} | {summary['mean_word_confidence']} | "
            f"{flags or 'none'} | {report_link} |"
        )
    if report["inventory_errors"]:
        lines.extend(["", "## PDF inventory errors", ""])
        for error in report["inventory_errors"]:
            lines.append(f"- `{error['book']}`: {error['error']}")
    if report["failed_pages"]:
        lines.extend(["", "## Failed pages and retries", ""])
        for page in report["failed_pages"]:
            lines.append(
                f"- `{page['book']}` page {page['page_number']}: "
                + "; ".join(page["errors"])
            )
    lines.extend(
        [
            "",
            "## Review notes",
            "",
            "- `english_only_candidate` uses the cached local IndicLID top label when available, with a Latin-letter fallback. It is a review flag, not proof that a page is English. Bengali and Assamese share much of their Unicode block; the classifier output is also not a correctness guarantee.",
            "- `low_confidence` means mean Tesseract word confidence below 60; confidence is not a calibrated probability of correctness.",
            "- Empty, script-mismatch, and suspicious-text pages are reported, not silently discarded. Inspect their page image and raw OCR.",
            "- The pilot intentionally does not process pages outside its selected sample. Use `--all-pages` only after explicit approval.",
            "",
        ]
    )
    if report["include_page_text"]:
        lines.extend(["## OCR text and page images", ""])
        for book in report["books"]:
            for record in book["records"]:
                lines.extend(
                    [
                        f"### {record['book']} — page {record['page_number']}",
                        "",
                        f"- Confidence: `{json.dumps(record['confidence'], ensure_ascii=False)}`",
                        f"- Local language ID: `{json.dumps(record.get('language_identification', {}), ensure_ascii=False)}`",
                        f"- Processing time: {record['page_elapsed_seconds']} s",
                        f"- Review flags: `{', '.join(record['review_flags'])}`",
                        f"- Page image: `{record['page_image'] or 'not retained'}`",
                        "",
                        "```text",
                        record["text"] or "[No text recognized]",
                        "```",
                        "",
                    ]
                )
    return "\n".join(lines)


def _configure_logger(log_path: Path) -> logging.Logger:
    logger = logging.getLogger("assamese_ocr")
    logger.setLevel(logging.INFO)
    logger.handlers.clear()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    return logger


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run a resumable Assamese OCR pilot by default. "
            "Corpus-wide processing requires the explicit --all-pages flag."
        )
    )
    parser.add_argument("--books-dir", type=Path, default=DEFAULT_BOOKS_DIR)
    parser.add_argument("--ocr-dir", type=Path, default=DEFAULT_OCR_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--tesseract-path", type=Path)
    parser.add_argument("--pilot-pages", type=int, default=DEFAULT_PILOT_PAGE_COUNT)
    parser.add_argument("--all-pages", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    args = parser.parse_args()
    if args.pilot_pages < 1:
        parser.error("--pilot-pages must be positive")
    if args.timeout_seconds < 1:
        parser.error("--timeout-seconds must be positive")
    if args.max_attempts < 1:
        parser.error("--max-attempts must be positive")
    if not args.books_dir.is_dir():
        parser.error(f"PDF books directory does not exist: {args.books_dir}")

    tesseract_path = _find_tesseract(args.tesseract_path)
    tesseract_version, installed_languages = _tesseract_info(tesseract_path)
    book_paths = sorted(
        args.books_dir.rglob("*.pdf"), key=lambda path: path.as_posix().casefold()
    )
    if not book_paths:
        parser.error(f"No PDF files found under {args.books_dir}")

    inventory = _inventory_books(book_paths)
    settings = {
        "renderer": "pypdfium2",
        "render_dpi": RENDER_DPI,
        "tesseract_version": tesseract_version,
        "language": OCR_LANGUAGE,
        "oem": OCR_OEM,
        "psm": OCR_PSM,
        "low_confidence_threshold": LOW_CONFIDENCE_THRESHOLD,
    }
    settings_id = hashlib.sha256(
        json.dumps(settings, sort_keys=True).encode("utf-8")
    ).hexdigest()[:12]
    plan = (
        [
            (book_index, page_number)
            for book_index, book in enumerate(inventory)
            if book["page_count"] is not None
            for page_number in range(1, int(book["page_count"]) + 1)
        ]
        if args.all_pages
        else _select_pilot_pages(inventory, args.pilot_pages)
    )
    run_started = time.perf_counter()
    run_id, run_dir = _new_run_directory(args.reports_dir)
    image_dir = run_dir / "page-images"
    book_report_dir = run_dir / "books"
    book_report_dir.mkdir(parents=True, exist_ok=True)
    logger = _configure_logger(run_dir / "ocr-run.log")
    language_model, language_classifier = _load_cached_language_model(logger)
    language_inference_rss = _current_process_tree_rss(psutil.Process(os.getpid()))
    logger.info(
        "Starting %s run: %s PDFs, %s selected pages, settings %s",
        "full" if args.all_pages else "pilot",
        len(book_paths),
        len(plan),
        settings_id,
    )

    selected_by_book: dict[int, list[int]] = {}
    for book_index, page_number in plan:
        selected_by_book.setdefault(book_index, []).append(page_number)
    all_records_by_book: dict[int, list[dict[str, Any]]] = {}
    newly_processed = 0
    reused = 0
    source_book_records: list[dict[str, Any]] = []
    for book_index, book in enumerate(inventory):
        selected_pages = selected_by_book.get(book_index, [])
        if not selected_pages:
            source_book_records.append(book)
            all_records_by_book[book_index] = []
            if book["inventory_error"]:
                logger.error("PDF inventory failed: %s: %s", book["book"], book["inventory_error"])
            continue
        source_book_records.append(book)
        book_hash = book["source_pdf_sha256"]
        document = None
        open_errors = []
        for attempt in range(1, args.max_attempts + 1):
            try:
                document = pdfium.PdfDocument(str(book_paths[book_index]))
                break
            except Exception as error:
                open_error = f"{type(error).__name__}: {error}"
                open_errors.append(open_error)
                logger.warning(
                    "PDF open failed: %s attempt %s/%s: %s",
                    book["book"],
                    attempt,
                    args.max_attempts,
                    open_error,
                )
                if attempt < args.max_attempts:
                    time.sleep(0.25)
        open_error = open_errors[-1] if open_errors else None

        records = []
        for page_number in selected_pages:
            page_json_path = _page_record_path(
                args.ocr_dir, settings_id, book, page_number
            )
            cached = _read_json(page_json_path)
            if _record_is_reusable(
                cached, source_sha256=book_hash, settings_id=settings_id
            ):
                if "language_identification" not in cached:
                    cached["language_identification"] = _classify_page_language(
                        language_model, cached.get("text", "")
                    )
                    cached["review_flags"] = _review_flags(
                        cached.get("text", ""),
                        cached.get("confidence", _parse_tsv_confidence("")),
                        cached["language_identification"],
                    )
                    cached["language_inference_rss_bytes"] = language_inference_rss
                    _atomic_write_json(page_json_path, cached)
                cached["processed_this_run"] = False
                records.append(cached)
                reused += 1
                logger.info("Reusing completed page: %s p.%s", book["book"], page_number)
                continue

            if open_error:
                errors = open_errors
                record = {
                    **book,
                    "page_number": page_number,
                    "status": "failed",
                    "settings_id": settings_id,
                    "render_dpi": RENDER_DPI,
                    "language": OCR_LANGUAGE,
                    "oem": OCR_OEM,
                    "psm": OCR_PSM,
                    "text": "",
                    "confidence": _parse_tsv_confidence(""),
                    "language_identification": {
                        "status": "unavailable",
                        "label": None,
                        "confidence": None,
                        "error": open_error,
                    },
                    "review_flags": ["pdf_open_failed", "human_review_required"],
                    "attempt_count": args.max_attempts,
                    "attempts": [
                        {"attempt": attempt, "result": "failed", "error": error}
                        for attempt, error in enumerate(open_errors, start=1)
                    ],
                    "errors": errors,
                    "page_image": None,
                    "page_image_sha256": None,
                    "ocr_elapsed_seconds": None,
                    "page_elapsed_seconds": None,
                    "peak_process_tree_rss_bytes": None,
                    "tesseract_warnings": [],
                }
            else:
                retained_image = image_dir / (
                    f"{_safe_stem(Path(book['book']))}-page-{page_number:06d}.png"
                )
                record = _process_page(
                    document=document,
                    book=book,
                    page_number=page_number,
                    settings_id=settings_id,
                    image_path=retained_image if not args.all_pages else None,
                    tesseract_path=tesseract_path,
                    timeout_seconds=args.timeout_seconds,
                    max_attempts=args.max_attempts,
                    logger=logger,
                    language_model=language_model,
                )
            record["processed_this_run"] = True
            _atomic_write_json(page_json_path, record)
            records.append(record)
            newly_processed += 1
            if record["status"] == "failed":
                logger.error(
                    "Page failed after %s attempts: %s p.%s",
                    record["attempt_count"],
                    book["book"],
                    page_number,
                )
            else:
                logger.info(
                    "Page complete: %s p.%s confidence=%s time=%ss flags=%s",
                    book["book"],
                    page_number,
                    record["confidence"]["mean"],
                    record["page_elapsed_seconds"],
                    ",".join(record["review_flags"]),
                )
        if document is not None:
            document.close()
        all_records_by_book[book_index] = records

    book_entries = []
    failed_pages = []
    peak_rss_values = []
    for book_index, book in enumerate(source_book_records):
        records = all_records_by_book.get(book_index, [])
        summary = _summarize_book(book, records)
        for record in records:
            if record["status"] == "failed":
                failed_pages.append(
                    {
                        "book": record["book"],
                        "page_number": record["page_number"],
                        "errors": record["errors"],
                    }
                )
            if record["peak_process_tree_rss_bytes"] is not None:
                peak_rss_values.append(record["peak_process_tree_rss_bytes"])
        report_path = None
        if records:
            per_book_name = f"{_safe_stem(Path(book['book']))}.md"
            per_book_path = book_report_dir / per_book_name
            per_book_path.write_text(
                _render_book_markdown(
                    summary,
                    records,
                    include_full_text=not args.all_pages,
                ),
                encoding="utf-8",
            )
            report_path = Path("books") / per_book_name
            (args.ocr_dir / "runs" / settings_id / "books").mkdir(
                parents=True, exist_ok=True
            )
            book_text_path = (
                args.ocr_dir
                / "runs"
                / settings_id
                / "books"
                / f"{_safe_stem(Path(book['book']))}_{book['source_pdf_sha256'][:12]}.txt"
            )
            text_lines = []
            page_record_dir = _page_record_path(
                args.ocr_dir, settings_id, book, 1
            ).parent
            for page_json in sorted(page_record_dir.glob("page-*.json")):
                record = _read_json(page_json)
                if record is None:
                    continue
                text_lines.append(
                    f"[PDF: {book['book']} | PAGE: {record['page_number']}]"
                )
                if record["status"] == "completed":
                    text_lines.append(record["text"])
                else:
                    text_lines.append(
                        f"[OCR FAILED after {record['attempt_count']} attempts; "
                        f"see page metadata: {', '.join(record['errors'])}]"
                    )
                text_lines.append("")
            book_text_path.write_text("\n".join(text_lines), encoding="utf-8")
        book_entries.append(
            {
                "summary": summary,
                "report_path": report_path.as_posix() if report_path else None,
                "records": (
                    records
                    if not args.all_pages
                    else [
                        {
                            key: value
                            for key, value in record.items()
                            if key not in {"text", "attempts"}
                        }
                        for record in records
                    ]
                ),
            }
        )

    total_pages = sum(
        int(book["page_count"])
        for book in inventory
        if book["page_count"] is not None
    )
    inventory_errors = [
        {"book": book["book"], "error": book["inventory_error"]}
        for book in inventory
        if book["inventory_error"]
    ]
    page_elapsed_values = [
        record["page_elapsed_seconds"]
        for records in all_records_by_book.values()
        for record in records
        if record["page_elapsed_seconds"] is not None
    ]
    report = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_id": run_id,
        "scope": "all PDF pages" if args.all_pages else "bounded balanced pilot",
        "pdf_count": len(inventory),
        "total_pages": total_pages,
        "selected_page_count": len(plan),
        "newly_processed_page_count": newly_processed,
        "reused_page_count": reused,
        "failed_page_count": len(failed_pages),
        "not_selected_page_count": max(total_pages - len(plan), 0),
        "page_ocr_total_elapsed_seconds": round(sum(page_elapsed_values), 3),
        "run_elapsed_seconds": round(time.perf_counter() - run_started, 3),
        "peak_page_ocr_process_tree_rss_bytes": max(peak_rss_values, default=None),
        "peak_process_tree_rss_bytes": max(
            [language_inference_rss, *peak_rss_values], default=None
        ),
        "memory_measurement_note": (
            "Peak RSS is sampled for the Python OCR runner and its live child processes; "
            "brief peaks between 100 ms samples can be missed."
        ),
        "renderer": "pypdfium2",
        "render_dpi": RENDER_DPI,
        "tesseract_path": str(tesseract_path),
        "tesseract_version": tesseract_version,
        "installed_languages": installed_languages,
        "language": OCR_LANGUAGE,
        "oem": OCR_OEM,
        "psm": OCR_PSM,
        "timeout_seconds": args.timeout_seconds,
        "max_attempts": args.max_attempts,
        "language_classifier": language_classifier,
        "language_inference_rss_bytes": language_inference_rss,
        "settings_id": settings_id,
        "source_books_directory": str(args.books_dir.resolve()),
        "ocr_output_directory": str(args.ocr_dir.resolve()),
        "reports_directory": str(run_dir.resolve()),
        "inventory_errors": inventory_errors,
        "failed_pages": failed_pages,
        "include_page_text": not args.all_pages,
        "books": book_entries,
    }
    report_path = run_dir / "report.json"
    markdown_path = run_dir / "report.md"
    _atomic_write_json(report_path, report)
    markdown_path.write_text(_render_overall_markdown(report), encoding="utf-8")
    logger.info(
        "Run complete: selected=%s newly_processed=%s reused=%s failed=%s not_selected=%s",
        len(plan),
        newly_processed,
        reused,
        len(failed_pages),
        max(total_pages - len(plan), 0),
    )
    print(f"\nREPORT={markdown_path}")
    print(f"DETAILS={report_path}")
    if args.all_pages:
        print("PAGE_IMAGES=not retained in full mode")
    elif image_dir.is_dir() and any(image_dir.iterdir()):
        print(f"PAGE_IMAGES={image_dir}")
    else:
        print("PAGE_IMAGES=see page-image paths in the report (reused cached pages)")
    print(f"OCR_OUTPUT={args.ocr_dir}")
    print(
        f"PDFS={len(inventory)} TOTAL_PAGES={total_pages} SELECTED={len(plan)} "
        f"NEW={newly_processed} REUSED={reused} FAILED={len(failed_pages)} "
        f"NOT_SELECTED={max(total_pages - len(plan), 0)} "
        f"PEAK_RSS_BYTES={report['peak_process_tree_rss_bytes']}"
    )
    return 1 if failed_pages or inventory_errors else 0


if __name__ == "__main__":
    sys.exit(main())
