from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import sys
import unicodedata
from typing import Any
import uuid


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OCR_DIR = PROJECT_ROOT / "data" / "ocr_text"
DEFAULT_CLEANED_DIR = PROJECT_ROOT / "data" / "cleaned_text"
DEFAULT_REPORTS_DIR = PROJECT_ROOT / "reports"
DEFAULT_TOKENIZER_DIR = PROJECT_ROOT / "checkpoints" / "kakugo-tokenizer"
TOKEN_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)
MANIFEST_VERSION = 1
MANIFEST_WARNING = (
    "Set review_status to approved only after checking the original PDF page image "
    "against the complete OCR transcription. Tesseract confidence and language "
    "classifier predictions are not proof of correctness."
)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(path)


def _load_page_records(ocr_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in sorted(ocr_dir.glob("runs/*/pages/*/page-*.json")):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeError(f"Unable to read OCR page metadata {path}: {error}") from error
        if not isinstance(record, dict):
            raise RuntimeError(f"OCR page metadata is not a JSON object: {path}")
        record["_metadata_path"] = str(path)
        records.append(record)
    if not records:
        raise FileNotFoundError(f"No page metadata JSON found under {ocr_dir}")
    return records


def create_review_manifest(ocr_dir: Path, manifest_path: Path) -> int:
    if manifest_path.exists():
        raise FileExistsError(
            f"Review manifest already exists and will not be overwritten: {manifest_path}"
        )
    pages = []
    records = _load_page_records(ocr_dir)
    for record in records:
        pages.append(
            {
                "book": record["book"],
                "source_relative_path": record["source_relative_path"],
                "source_pdf_sha256": record["source_pdf_sha256"],
                "page_number": record["page_number"],
                "ocr_status": record["status"],
                "ocr_settings_id": record["settings_id"],
                "ocr_text_sha256": hashlib.sha256(
                    record.get("text", "").encode("utf-8")
                ).hexdigest(),
                "review_status": "pending",
                "reviewed_by": "",
                "reviewed_at": "",
                "review_notes": "",
            }
        )
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    _atomic_write_json(
        manifest_path,
        {
            "version": MANIFEST_VERSION,
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "instructions": MANIFEST_WARNING,
            "pages": pages,
        },
    )
    return len(pages)


def _word_tokens(text: str) -> list[str]:
    return [match.group(0).casefold() for match in TOKEN_PATTERN.finditer(text)]


def _character_distribution(text: str) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for character in text:
        if character.isspace():
            continue
        category = unicodedata.category(character)
        if category.startswith("L"):
            group = "assamese_bengali_unicode_block" if "\u0980" <= character <= "\u09ff" else "other_letters"
        elif category.startswith("M"):
            group = "combining_marks"
        elif category.startswith("N"):
            group = "numbers"
        elif category.startswith("P"):
            group = "punctuation"
        elif category.startswith("S"):
            group = "symbols"
        elif category.startswith("C"):
            group = "control_or_format"
        else:
            group = "other"
        counts[group] += 1
    return dict(sorted(counts.items()))


def _tokenizer_counts(texts: list[str], tokenizer_dir: Path) -> dict[str, Any]:
    if not tokenizer_dir.is_dir():
        return {
            "status": "unavailable",
            "tokenizer_path": str(tokenizer_dir),
            "error": (
                "Exact Kakugo tokenizer files are not available locally. "
                "No tokenizer or model files were downloaded."
            ),
            "train_tokens": None,
            "validation_tokens": None,
        }
    try:
        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(
            str(tokenizer_dir),
            local_files_only=True,
            trust_remote_code=False,
        )
        return {
            "status": "counted",
            "tokenizer_path": str(tokenizer_dir),
            "train_tokens": sum(
                len(tokenizer.encode(text, add_special_tokens=False))
                for text in texts
            ),
            "validation_tokens": None,
            "error": None,
        }
    except Exception as error:
        return {
            "status": "error",
            "tokenizer_path": str(tokenizer_dir),
            "error": f"{type(error).__name__}: {error}",
            "train_tokens": None,
            "validation_tokens": None,
        }


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"Unable to read review manifest {path}: {error}") from error
    if not isinstance(manifest, dict) or manifest.get("version") != MANIFEST_VERSION:
        raise ValueError(f"Unsupported or invalid review manifest: {path}")
    if not isinstance(manifest.get("pages"), list):
        raise ValueError("Review manifest 'pages' must be a list.")
    return manifest


def _approved_page_keys(manifest: dict[str, Any]) -> dict[tuple[str, str, int], dict[str, Any]]:
    approved = {}
    seen = set()
    for item in manifest["pages"]:
        if not isinstance(item, dict):
            raise ValueError("Every review manifest page entry must be an object.")
        key = (
            str(item.get("source_relative_path", "")),
            str(item.get("source_pdf_sha256", "")),
            int(item.get("page_number", 0)),
        )
        if not all(key) or key[2] < 1:
            raise ValueError(f"Invalid source identity in review manifest entry: {item}")
        if key in seen:
            raise ValueError(f"Duplicate review manifest page entry: {key}")
        seen.add(key)
        status = item.get("review_status")
        if status not in {"pending", "approved", "excluded", "needs_correction"}:
            raise ValueError(f"Invalid review status {status!r} for {key}")
        if status == "approved":
            if item.get("ocr_status") != "completed":
                raise ValueError(f"Cannot approve a page whose OCR failed: {key}")
            if not str(item.get("reviewed_by", "")).strip():
                raise ValueError(f"Approved page must identify reviewer: {key}")
            reviewed_at = str(item.get("reviewed_at", "")).strip()
            if not reviewed_at:
                raise ValueError(f"Approved page must have reviewed_at timestamp: {key}")
            try:
                datetime.fromisoformat(reviewed_at.replace("Z", "+00:00"))
            except ValueError as error:
                raise ValueError(f"Invalid reviewed_at timestamp for {key}") from error
            approved[key] = item
    return approved


def _book_validation_split(book_id: str, validation_fraction: float) -> str:
    value = int(hashlib.sha256(book_id.encode("utf-8")).hexdigest()[:16], 16)
    return (
        "validation"
        if value / float(0xFFFFFFFFFFFFFFFF) < validation_fraction
        else "train"
    )


def _assign_book_splits(
    book_ids: list[str], validation_fraction: float
) -> dict[str, str]:
    if len(book_ids) < 2:
        return {book_id: "train" for book_id in book_ids}
    splits = {
        book_id: _book_validation_split(book_id, validation_fraction)
        for book_id in book_ids
    }
    if "validation" not in splits.values():
        validation_book = min(
            book_ids,
            key=lambda book_id: hashlib.sha256(book_id.encode("utf-8")).hexdigest(),
        )
        splits[validation_book] = "validation"
    if "train" not in splits.values():
        train_book = max(
            book_ids,
            key=lambda book_id: hashlib.sha256(book_id.encode("utf-8")).hexdigest(),
        )
        splits[train_book] = "train"
    return splits


def build_training_corpus(
    *,
    ocr_dir: Path,
    manifest_path: Path,
    output_dir: Path,
    reports_dir: Path,
    tokenizer_dir: Path,
    validation_fraction: float,
) -> dict[str, Any]:
    if not 0.0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be > 0 and < 0.5.")
    manifest = _load_manifest(manifest_path)
    approved = _approved_page_keys(manifest)
    records = _load_page_records(ocr_dir)
    records_by_book: dict[str, list[tuple[dict[str, Any], dict[str, Any]]]] = {}
    manifest_page_keys = set()
    for record in records:
        key = (
            record["source_relative_path"],
            record["source_pdf_sha256"],
            int(record["page_number"]),
        )
        manifest_page_keys.add(key)
        entry = approved.get(key)
        if entry is None:
            continue
        if record["status"] != "completed":
            raise ValueError(f"Manifest approval does not match completed OCR page {key}")
        text_digest = hashlib.sha256(record.get("text", "").encode("utf-8")).hexdigest()
        if entry.get("ocr_text_sha256") != text_digest:
            raise ValueError(f"OCR text changed since page review; review again: {key}")
        if entry.get("ocr_settings_id") != record.get("settings_id"):
            raise ValueError(f"OCR settings changed since page review: {key}")
        records_by_book.setdefault(record["source_relative_path"], []).append(
            (record, entry)
        )

    missing_approved_pages = set(approved) - manifest_page_keys
    if missing_approved_pages:
        raise ValueError(
            f"{len(missing_approved_pages)} approved pages do not match current OCR metadata."
        )
    if not records_by_book:
        raise ValueError(
            "No human-reviewed pages are approved. No cleaned corpus was written."
        )
    book_ids = sorted(records_by_book)
    splits = _assign_book_splits(book_ids, validation_fraction)
    if len(book_ids) < 2 or set(splits.values()) != {"train", "validation"}:
        raise ValueError(
            "At least two books with human-reviewed approved pages are needed for "
            "book-disjoint train and validation splits. No corpus was written."
        )

    split_texts: dict[str, list[str]] = {"train": [], "validation": []}
    page_counts: Counter[str] = Counter()
    character_counts: Counter[str] = Counter()
    confidence_values = []
    review_flag_counts: Counter[str] = Counter()
    duplicate_fingerprints: dict[str, list[dict[str, Any]]] = {}
    books_report = []
    for book_id in book_ids:
        split = splits[book_id]
        reviewed_records = sorted(
            records_by_book[book_id],
            key=lambda reviewed: int(reviewed[0]["page_number"]),
        )
        if not reviewed_records:
            continue
        book_text_parts = []
        approved_numbers = []
        for record, entry in reviewed_records:
            text = record["text"]
            corrected_path = entry.get("corrected_text_path")
            if corrected_path:
                if manifest_path.parent.name == "training_data" and (
                    manifest_path.parent.parent.name == "data"
                ):
                    project_root = manifest_path.parent.parent.parent
                else:
                    project_root = manifest_path.parent
                corrected_file = (project_root / Path(corrected_path)).resolve()
                if not corrected_file.is_relative_to(project_root.resolve()):
                    raise ValueError(
                        f"Corrected OCR path must remain inside the project: {corrected_path}"
                    )
                try:
                    corrected_text = corrected_file.read_text(encoding="utf-8")
                except OSError as error:
                    raise RuntimeError(
                        f"Unable to read reviewed correction {corrected_file}: {error}"
                    ) from error
                corrected_digest = hashlib.sha256(
                    corrected_text.encode("utf-8")
                ).hexdigest()
                if corrected_digest != entry.get("corrected_text_sha256"):
                    raise ValueError(
                        f"Corrected OCR text changed since review: {corrected_file}"
                    )
                text = corrected_text
            if not text.strip():
                raise ValueError(
                    f"Reviewed page has empty OCR text and cannot enter corpus: "
                    f"{record['book']} page {record['page_number']}"
                )
            book_text_parts.append(
                f"[BOOK: {record['book']} | PDF PAGE: {record['page_number']}]\n{text}"
            )
            split_texts[split].append(text)
            page_counts[split] += 1
            character_counts[split] += len(text)
            approved_numbers.append(int(record["page_number"]))
            confidence = record.get("confidence", {}).get("mean")
            if isinstance(confidence, (int, float)):
                confidence_values.append(float(confidence))
            review_flag_counts.update(record.get("review_flags", []))
            normalized = " ".join(text.split()).casefold()
            if normalized:
                fingerprint = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                duplicate_fingerprints.setdefault(fingerprint, []).append(
                    {
                        "book": record["book"],
                        "page_number": int(record["page_number"]),
                    }
                )
        safe_name = (
            re.sub(r'[<>:"/\\|?*]+', "_", Path(book_id).stem).strip(" .")
            + "_"
            + hashlib.sha256(book_id.encode("utf-8")).hexdigest()[:10]
        )
        destination = output_dir / split / f"{safe_name}.txt"
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            raise FileExistsError(
                f"Refusing to overwrite an existing corpus file: {destination}"
            )
        with destination.open("x", encoding="utf-8", newline="\n") as output_file:
            output_file.write("\n\n".join(book_text_parts) + "\n")
        corrected_page_count = sum(
            bool(entry.get("corrected_text_path")) for _, entry in reviewed_records
        )
        if corrected_page_count == len(reviewed_records):
            text_source = "human-corrected OCR"
        elif corrected_page_count:
            text_source = "mixed human-corrected and approved raw OCR"
        else:
            text_source = "human-approved raw OCR"
        books_report.append(
            {
                "book": reviewed_records[0][0]["book"],
                "source_relative_path": book_id,
                "split": split,
                "approved_page_numbers": approved_numbers,
                "approved_page_count": len(approved_numbers),
                "text_source": text_source,
                "output_path": str(destination),
            }
        )

    all_text = {
        split: "\n".join(texts) for split, texts in split_texts.items()
    }
    word_counts = {
        split: _word_tokens(text) for split, text in all_text.items()
    }
    vocabulary = {
        split: len(set(tokens)) for split, tokens in word_counts.items()
    }
    vocabulary_frequency = Counter(word_counts["train"])
    tokenizer = _tokenizer_counts(
        [all_text["train"], all_text["validation"]], tokenizer_dir
    )
    if tokenizer["status"] == "counted":
        from transformers import AutoTokenizer

        local_tokenizer = AutoTokenizer.from_pretrained(
            str(tokenizer_dir), local_files_only=True, trust_remote_code=False
        )
        tokenizer["train_tokens"] = len(
            local_tokenizer.encode(all_text["train"], add_special_tokens=False)
        )
        tokenizer["validation_tokens"] = len(
            local_tokenizer.encode(all_text["validation"], add_special_tokens=False)
        )
        tokenizer["vocabulary_size"] = len(local_tokenizer)
    report = {
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "review_manifest": str(manifest_path),
        "ocr_directory": str(ocr_dir),
        "cleaned_corpus_directory": str(output_dir),
        "validation_strategy": (
            "Deterministic split by source book path; pages from one book cannot occur "
            "in both splits. No page-level random split."
        ),
        "validation_fraction_target": validation_fraction,
        "train_pages": page_counts["train"],
        "validation_pages": page_counts["validation"],
        "train_characters": character_counts["train"],
        "validation_characters": character_counts["validation"],
        "train_whitespace_words": len(all_text["train"].split()),
        "validation_whitespace_words": len(all_text["validation"].split()),
        "train_distinct_whitespace_tokens": vocabulary["train"],
        "validation_distinct_whitespace_tokens": vocabulary["validation"],
        "train_top_50_whitespace_tokens": vocabulary_frequency.most_common(50),
        "approved_ocr_confidence": {
            "pages_with_score": len(confidence_values),
            "mean": (
                round(sum(confidence_values) / len(confidence_values), 2)
                if confidence_values
                else None
            ),
            "minimum": round(min(confidence_values), 2) if confidence_values else None,
            "below_60_pages": sum(value < 60 for value in confidence_values),
            "warning": "Tesseract confidence is not a calibrated probability or proof of correctness.",
        },
        "approved_review_flag_counts": dict(sorted(review_flag_counts.items())),
        "exact_duplicate_approved_page_groups": [
            pages
            for pages in duplicate_fingerprints.values()
            if len(pages) > 1
        ],
        "character_distribution": {
            split: _character_distribution(text)
            for split, text in all_text.items()
        },
        "tokenizer_counts": tokenizer,
        "cleaning_policy": (
            "No automatic rewriting, translation, punctuation normalization, "
            "header/footer removal, or deduplication. Human corrections are read "
            "from separate corrected OCR files; page/book boundaries and approved "
            "text are retained verbatim."
        ),
        "unreviewed_page_count": sum(
            item.get("review_status") == "pending" for item in manifest["pages"]
        ),
        "excluded_page_count": sum(
            item.get("review_status") in {"excluded", "rejected"}
            for item in manifest["pages"]
        ),
        "rejected_page_count": sum(
            item.get("review_status") in {"excluded", "rejected"}
            for item in manifest["pages"]
        ),
        "needs_correction_page_count": sum(
            item.get("review_status") == "needs_correction"
            for item in manifest["pages"]
        ),
        "approved_page_count": len(approved),
        "books": books_report,
        "notes": [
            "Only pages explicitly approved by a named human reviewer with a timestamp are included.",
            "Review approval must compare the complete OCR transcription with the original rendered PDF page.",
            "OCR confidence and automated language labels are not treated as proof of correctness.",
            "Text from pending, needs-correction, and rejected pages is not written to the cleaned training corpus.",
            "Whitespace token counts and distinct whitespace token counts are estimates, not model-tokenizer counts.",
        ],
    }
    reports_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().astimezone().strftime("%Y%m%d-%H%M%S")
    report_path = reports_dir / f"training-corpus-quality-{timestamp}-{uuid.uuid4().hex[:8]}.json"
    _atomic_write_json(report_path, report)
    report["report_path"] = str(report_path)
    markdown_path = report_path.with_suffix(".md")
    markdown_path.write_text(_render_report_markdown(report), encoding="utf-8")
    report["markdown_report_path"] = str(markdown_path)
    return report


def _render_report_markdown(report: dict[str, Any]) -> str:
    tokenizer = report["tokenizer_counts"]
    lines = [
        "# Reviewed Assamese OCR Training Corpus",
        "",
        f"- Generated: {report['created_at']}",
        f"- Review manifest: `{report['review_manifest']}`",
        f"- Cleaned corpus: `{report['cleaned_corpus_directory']}`",
        f"- Approved pages: {report['approved_page_count']}",
        f"- Pending pages: {report['unreviewed_page_count']}",
        f"- Needs-correction pages: {report['needs_correction_page_count']}",
        f"- Rejected pages: {report['rejected_page_count']}",
        f"- Train pages: {report['train_pages']}; characters: {report['train_characters']}; "
        f"whitespace words: {report['train_whitespace_words']}; "
        f"distinct whitespace tokens: {report['train_distinct_whitespace_tokens']}",
        f"- Validation pages: {report['validation_pages']}; "
        f"characters: {report['validation_characters']}; "
        f"whitespace words: {report['validation_whitespace_words']}; "
        f"distinct whitespace tokens: {report['validation_distinct_whitespace_tokens']}",
        f"- Exact tokenizer status: {tokenizer['status']}",
        f"- Exact train/validation tokenizer tokens: "
        f"{tokenizer.get('train_tokens')} / {tokenizer.get('validation_tokens')}",
        "",
        "## Book-level split",
        "",
        "| Book | Split | Approved pages | Output |",
        "|---|---|---:|---|",
    ]
    for book in report["books"]:
        output = Path(book["output_path"]).as_posix()
        lines.append(
            f"| {book['book']} | {book['split']} | {book['approved_page_count']} "
            f"| `{output}` |"
        )
    lines.extend(["", "## Character distribution", ""])
    for split, distribution in report["character_distribution"].items():
        lines.extend(
            [
                f"### {split}",
                "",
                "| Unicode category | Count |",
                "|---|---:|",
            ]
        )
        lines.extend(
            f"| {category} | {count} |" for category, count in distribution.items()
        )
        lines.append("")
    lines.extend(
        [
            "## Most frequent training whitespace tokens",
            "",
            "Counts are simple whitespace/Unicode word estimates, not Granite tokenizer counts.",
            "",
            "| Token | Count |",
            "|---|---:|",
        ]
    )
    lines.extend(
        f"| `{token}` | {count} |"
        for token, count in report["train_top_50_whitespace_tokens"]
    )
    lines.extend(
        [
            "## Training-data and quality safeguards",
            "",
            *[f"- {note}" for note in report["notes"]],
            f"- Cleaning policy: {report['cleaning_policy']}",
            "- Assamese and Bengali share much of the measured Unicode block; character distribution is not Assamese language identification.",
            "- Whitespace token counts are corpus-size estimates, not model tokenizer counts.",
            f"- Approved-page Tesseract confidence summary (not accuracy): `{json.dumps(report['approved_ocr_confidence'], ensure_ascii=False)}`",
            f"- Exact duplicate approved-page text groups flagged for human inspection (not removed): `{json.dumps(report['exact_duplicate_approved_page_groups'], ensure_ascii=False)}`",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Create a human page-review manifest or build a book-disjoint corpus "
            "from explicitly approved OCR pages."
        )
    )
    parser.add_argument("--ocr-dir", type=Path, default=DEFAULT_OCR_DIR)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--create-review-manifest", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument(
        "--allow-unreviewed-ocr",
        action="store_true",
        help=(
            "Build a separate automatically filtered corpus from raw OCR without "
            "changing the human-review manifest."
        ),
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_CLEANED_DIR)
    parser.add_argument("--reports-dir", type=Path, default=DEFAULT_REPORTS_DIR)
    parser.add_argument("--tokenizer-dir", type=Path, default=DEFAULT_TOKENIZER_DIR)
    parser.add_argument("--validation-fraction", type=float, default=0.1)
    args = parser.parse_args()
    if args.create_review_manifest == args.build:
        parser.error("Choose exactly one of --create-review-manifest or --build.")
    if args.allow_unreviewed_ocr and not args.build:
        parser.error("--allow-unreviewed-ocr requires --build.")
    if args.manifest is None:
        parser.error("--manifest is required.")
    if args.create_review_manifest:
        page_count = create_review_manifest(args.ocr_dir, args.manifest)
        print(f"REVIEW_MANIFEST={args.manifest}")
        print(f"PAGES_REQUIRING_REVIEW={page_count}")
        print("No cleaned dataset was created.")
        return 0
    if args.allow_unreviewed_ocr:
        from scripts.automatic_corpus import build_automatic_corpus

        report = build_automatic_corpus(
            ocr_dir=args.ocr_dir,
            manifest_path=args.manifest,
            training_data_dir=args.manifest.parent,
            reports_dir=args.reports_dir,
            tokenizer_dir=args.tokenizer_dir,
            validation_fraction=args.validation_fraction,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    report = build_training_corpus(
        ocr_dir=args.ocr_dir,
        manifest_path=args.manifest,
        output_dir=args.output_dir,
        reports_dir=args.reports_dir,
        tokenizer_dir=args.tokenizer_dir,
        validation_fraction=args.validation_fraction,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
