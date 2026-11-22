from __future__ import annotations

from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import unicodedata
from typing import Any


MIN_ASSAMESE_LETTERS = 40
MIN_TOTAL_LETTERS = 80
MIN_ASSAMESE_LETTER_RATIO = 0.30
MIN_OCR_CONFIDENCE = 30.0
LOW_CONFIDENCE_THRESHOLD = 60.0
EXPECTED_KAKUGO_VOCAB_SIZE = 100_352
TOKENIZER_REVISION = "a6a854a0a680c4c57ec026df014f8f5964da8721"
TOKENIZER_REPOSITORY = "ptrdvn/kakugo-3B-asm"
REPEATED_GLYPH = re.compile(r"([^\s])\1{12,}")
WORD_PATTERN = re.compile(r"[^\W_]+(?:['’][^\W_]+)*", re.UNICODE)


class AutomaticCorpusError(RuntimeError):
    pass


def _read_records(ocr_dir: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for metadata_path in sorted(ocr_dir.glob("runs/*/pages/*/page-*.json")):
        try:
            record = json.loads(metadata_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AutomaticCorpusError(
                f"Unable to read OCR page metadata {metadata_path}: {error}"
            ) from error
        if not isinstance(record, dict):
            raise AutomaticCorpusError(
                f"OCR page metadata is not a JSON object: {metadata_path}"
            )
        record["_metadata_path"] = str(metadata_path)
        records.append(record)
    if not records:
        raise FileNotFoundError(f"No OCR page records found under {ocr_dir}")
    return records


def _page_key(record: dict[str, Any]) -> tuple[str, str, int]:
    return (
        str(record.get("source_relative_path", "")),
        str(record.get("source_pdf_sha256", "")),
        int(record.get("page_number", 0)),
    )


def _tokenizer_counts(texts: list[str], tokenizer_dir: Path) -> tuple[list[int], dict[str, Any]]:
    try:
        from transformers import AutoTokenizer
    except ImportError:
        estimated = [
            max(1, math.ceil(len(text) / 3.0)) if text else 0 for text in texts
        ]
        return estimated, {
            "status": "approximate",
            "tokenizer_repository": TOKENIZER_REPOSITORY,
            "tokenizer_revision": TOKENIZER_REVISION,
            "tokenizer_path": str(tokenizer_dir),
            "error": (
                "Transformers is unavailable in this Python environment. Counts use "
                "ceil(text characters / 3) and are only rough estimates."
            ),
        }
    if not tokenizer_dir.is_dir():
        raise FileNotFoundError(
            f"Kakugo tokenizer directory is missing: {tokenizer_dir}. "
            "Download only the small tokenizer files before building this dataset."
        )
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(tokenizer_dir),
            local_files_only=True,
            trust_remote_code=False,
        )
    except Exception as error:
        raise AutomaticCorpusError(
            f"Unable to load the pinned local Kakugo tokenizer: {error}"
        ) from error
    if len(tokenizer) != EXPECTED_KAKUGO_VOCAB_SIZE:
        raise AutomaticCorpusError(
            f"Kakugo tokenizer vocabulary mismatch: expected "
            f"{EXPECTED_KAKUGO_VOCAB_SIZE}, got {len(tokenizer)}."
        )
    return (
        [
            len(tokenizer.encode(text, add_special_tokens=False)) if text else 0
            for text in texts
        ],
        {
            "status": "exact",
            "tokenizer_repository": TOKENIZER_REPOSITORY,
            "tokenizer_revision": TOKENIZER_REVISION,
            "tokenizer_path": str(tokenizer_dir),
            "tokenizer_class": type(tokenizer).__name__,
            "vocabulary_size": len(tokenizer),
            "error": None,
        },
    )


def _classify_page(record: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    text = str(record.get("text", ""))
    flags = set(record.get("review_flags") or [])
    language = record.get("language_identification") or {}
    letters = [character for character in text if character.isalpha()]
    assamese_letters = [
        character for character in letters if "\u0980" <= character <= "\u09ff"
    ]
    other_letters = len(letters) - len(assamese_letters)
    assamese_ratio = len(assamese_letters) / len(letters) if letters else 0.0
    non_assamese_ratio = other_letters / len(letters) if letters else 0.0
    confidence = (record.get("confidence") or {}).get("mean")
    label = language.get("label")
    book_name = str(record.get("book", "")).casefold()
    reasons: list[str] = []

    if "bengali medium" in book_name:
        reasons.append("non_assamese_medium_book")
    if record.get("status") != "completed":
        reasons.append("ocr_failed")
    if not text.strip():
        reasons.append("empty_page")
    if len(letters) < MIN_TOTAL_LETTERS:
        reasons.append("too_short")
    if (
        len(assamese_letters) < MIN_ASSAMESE_LETTERS
        or assamese_ratio < MIN_ASSAMESE_LETTER_RATIO
    ):
        reasons.append("insufficient_assamese_script")

    if confidence is not None and float(confidence) < MIN_OCR_CONFIDENCE:
        reasons.append("very_low_ocr_confidence")
    if (
        "bengali_or_non_assamese_candidate" in flags
        or label in {"ben_Beng", "ben"}
    ):
        reasons.append("bengali_or_non_assamese_candidate")
    if "english_only_candidate" in flags and len(assamese_letters) < MIN_ASSAMESE_LETTERS:
        reasons.append("english_only_candidate")
    if "language_uncertain" in flags:
        reasons.append("uncertain_language")
    if (
        language.get("status") == "classified"
        and label
        and label not in {"asm_Beng", "asm"}
        and label not in {"ben_Beng", "ben"}
        and len(assamese_letters) < MIN_ASSAMESE_LETTERS
    ):
        reasons.append("other_non_assamese_language")

    invalid_characters = 0
    for character in text:
        category = unicodedata.category(character)
        if (
            character == "\ufffd"
            or category in {"Cc", "Cs", "Co", "Cn"}
            and character not in "\n\r\t"
        ):
            invalid_characters += 1
    if invalid_characters:
        reasons.append("corrupt_unicode_or_control_characters")
    if REPEATED_GLYPH.search(text):
        reasons.append("repeated_ocr_artifact")

    visible = [character for character in text if not character.isspace()]
    symbol_noise = sum(
        unicodedata.category(character).startswith("S")
        or unicodedata.category(character) == "Co"
        for character in visible
    )
    if len(visible) >= 100 and symbol_noise / len(visible) > 0.55:
        reasons.append("excessive_symbol_artifacts")
    if non_assamese_ratio > 1.0 - MIN_ASSAMESE_LETTER_RATIO:
        reasons.append("excessive_non_assamese_letters")

    metrics = {
        "total_letters": len(letters),
        "assamese_unicode_letters": len(assamese_letters),
        "assamese_letter_ratio": round(assamese_ratio, 4),
        "non_assamese_letter_ratio": round(non_assamese_ratio, 4),
        "mean_ocr_confidence": confidence,
        "language_label": label,
        "language_confidence": language.get("confidence"),
        "review_flags": sorted(flags),
    }
    return sorted(set(reasons)), metrics


def _split_books(book_ids: list[str], validation_fraction: float) -> dict[str, str]:
    if not 0.0 < validation_fraction < 0.5:
        raise ValueError("validation_fraction must be greater than 0 and below 0.5.")
    if len(book_ids) < 2:
        raise ValueError(
            "At least two books with automatically accepted pages are required "
            "for a book-disjoint train/validation split."
        )
    ordered = sorted(
        book_ids,
        key=lambda book_id: hashlib.sha256(book_id.encode("utf-8")).hexdigest(),
    )
    validation_count = min(
        len(ordered) - 1,
        max(1, round(len(ordered) * validation_fraction)),
    )
    validation = set(ordered[:validation_count])
    return {
        book_id: "validation" if book_id in validation else "train"
        for book_id in book_ids
    }


def _write_new_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as output:
        output.write(content)


def build_automatic_corpus(
    *,
    ocr_dir: Path,
    manifest_path: Path,
    training_data_dir: Path,
    reports_dir: Path,
    tokenizer_dir: Path,
    validation_fraction: float = 0.2,
) -> dict[str, Any]:
    if not manifest_path.is_file():
        raise FileNotFoundError(f"Review manifest not found: {manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise AutomaticCorpusError(f"Unable to read review manifest: {error}") from error
    if not isinstance(manifest, dict) or not isinstance(manifest.get("pages"), list):
        raise ValueError(f"Invalid review manifest: {manifest_path}")
    manifest_by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    for page in manifest["pages"]:
        if not isinstance(page, dict):
            raise ValueError("Every review manifest page must be an object.")
        key = _page_key(page)
        if not all(key) or key[2] < 1 or key in manifest_by_key:
            raise ValueError(f"Invalid or duplicate review manifest page identity: {key}")
        manifest_by_key[key] = page

    records = _read_records(ocr_dir)
    record_by_key: dict[tuple[str, str, int], dict[str, Any]] = {}
    for record in records:
        key = _page_key(record)
        if not all(key) or key[2] < 1 or key in record_by_key:
            raise ValueError(f"Invalid or duplicate OCR page identity: {key}")
        record_by_key[key] = record
    missing_ocr = set(manifest_by_key) - set(record_by_key)
    if missing_ocr:
        raise ValueError(
            f"{len(missing_ocr)} manifest pages have no matching OCR metadata. "
            "Refusing to silently omit pages."
        )
    unmanifested_ocr = set(record_by_key) - set(manifest_by_key)
    if unmanifested_ocr:
        raise ValueError(
            f"{len(unmanifested_ocr)} OCR pages are not represented in the review "
            "manifest. Resolve the inventory mismatch before filtering."
        )

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    accepted_digests: set[str] = set()
    seen_ocr_keys: set[tuple[str, str, int]] = set()
    duplicate_count = 0
    for record in sorted(
        records,
        key=lambda item: (
            str(item.get("source_relative_path", "")),
            int(item.get("page_number", 0)),
        ),
    ):
        key = _page_key(record)
        manifest_page = manifest_by_key[key]
        reasons, metrics = _classify_page(record)
        if manifest_page.get("review_status") in {"excluded", "rejected"}:
            reasons.append("already_rejected_in_review_manifest")
        elif manifest_page.get("review_status") == "needs_correction":
            reasons.append("needs_correction_in_review_manifest")
        raw_text = str(record.get("text", ""))
        normalized = " ".join(raw_text.split()).casefold()
        text_digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        if normalized and text_digest in accepted_digests:
            reasons.append("duplicate_page")
            duplicate_count += 1
        if key in seen_ocr_keys:
            reasons.append("duplicate_page_identity")
        seen_ocr_keys.add(key)

        common = {
            "book": record.get("book"),
            "source_relative_path": record.get("source_relative_path"),
            "source_pdf_sha256": record.get("source_pdf_sha256"),
            "page_number": int(record.get("page_number", 0)),
            "ocr_settings_id": record.get("settings_id"),
            "ocr_status": record.get("status"),
            "ocr_text_sha256": hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
            "review_status_at_filter_time": manifest_page.get("review_status"),
            "review_manifest_was_modified": False,
            "ocr_metadata_path": record.get("_metadata_path"),
            "text": raw_text,
            **metrics,
        }
        reasons = sorted(set(reasons))
        if reasons:
            rejected.append({**common, "rejection_reasons": reasons})
        else:
            accepted_digests.add(text_digest)
            accepted.append({**common, "approximate_text_sha256": text_digest})

    accepted_by_book: dict[str, list[dict[str, Any]]] = {}
    for item in accepted:
        accepted_by_book.setdefault(item["source_relative_path"], []).append(item)
    split_error = None
    try:
        splits = _split_books(sorted(accepted_by_book), validation_fraction)
    except ValueError as error:
        splits = {}
        split_error = str(error)

    auto_jsonl = training_data_dir / "auto_filtered_assamese.jsonl"
    auto_txt = training_data_dir / "auto_filtered_assamese.txt"
    rejected_jsonl = training_data_dir / "auto_rejected_pages.jsonl"
    processed_dir = training_data_dir / "processed"
    train_jsonl = processed_dir / "train.jsonl"
    validation_jsonl = processed_dir / "validation.jsonl"
    train_txt = processed_dir / "train.txt"
    validation_txt = processed_dir / "validation.txt"
    split_manifest_path = processed_dir / "split-manifest.json"
    report_path = reports_dir / "automatic-corpus-quality-report.md"
    targets = [
        auto_jsonl,
        auto_txt,
        rejected_jsonl,
        report_path,
    ]
    if splits:
        targets.extend(
            [
                train_jsonl,
                validation_jsonl,
                train_txt,
                validation_txt,
                split_manifest_path,
            ]
        )
    existing = [str(path) for path in targets if path.exists()]
    if existing:
        raise FileExistsError(
            "Refusing to overwrite automatic corpus outputs: " + ", ".join(existing)
        )

    tokenizer_source_texts = [item["text"] for item in accepted]
    token_counts, tokenizer_info = _tokenizer_counts(
        tokenizer_source_texts, tokenizer_dir
    )
    accepted_rows: list[dict[str, Any]] = []
    for item, token_count in zip(accepted, token_counts):
        accepted_rows.append(
            {
                **item,
                "token_count": token_count,
                "tokenizer_repository": TOKENIZER_REPOSITORY,
                "tokenizer_revision": TOKENIZER_REVISION,
            }
        )
    accepted_by_book.clear()
    for item in accepted_rows:
        accepted_by_book.setdefault(item["source_relative_path"], []).append(item)

    train_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    per_book_counts = []
    if splits:
        for book_id in sorted(accepted_by_book):
            book_rows = sorted(
                accepted_by_book[book_id],
                key=lambda item: item["page_number"],
            )
            target_rows = (
                validation_rows if splits[book_id] == "validation" else train_rows
            )
            target_rows.extend(book_rows)
            per_book_counts.append(
                {
                    "book": book_rows[0]["book"],
                    "source_relative_path": book_id,
                    "split": splits[book_id],
                    "accepted_pages": len(book_rows),
                    "characters": sum(len(item["text"]) for item in book_rows),
                    "tokens": sum(item["token_count"] for item in book_rows),
                }
            )

    low_confidence_pages = sum(
        isinstance((record.get("confidence") or {}).get("mean"), (int, float))
        and float(record["confidence"]["mean"]) < LOW_CONFIDENCE_THRESHOLD
        for record in records
    )
    empty_pages = sum(not str(record.get("text", "")).strip() for record in records)
    non_assamese_candidates = sum(
        bool(
            set(record.get("review_flags") or [])
            & {"english_only_candidate", "bengali_or_non_assamese_candidate"}
        )
        or (
            (record.get("language_identification") or {}).get("label")
            not in {None, "asm_Beng", "asm"}
            and (record.get("language_identification") or {}).get("status")
            == "classified"
        )
        for record in records
    )
    reason_counts = Counter(
        reason for item in rejected for reason in item["rejection_reasons"]
    )
    accepted_text = "\n".join(item["text"] for item in accepted_rows)
    words = WORD_PATTERN.findall(accepted_text)
    approximate_character_count = sum(len(item["text"]) for item in accepted_rows)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    report: dict[str, Any] = {
        "created_at": created_at,
        "dataset_type": "automatically filtered OCR; not human-reviewed or error-free",
        "manifest_path": str(manifest_path),
        "manifest_modified": False,
        "ocr_directory": str(ocr_dir),
        "total_pages": len(records),
        "accepted_pages": len(accepted_rows),
        "rejected_pages": len(rejected),
        "empty_pages": empty_pages,
        "low_confidence_pages_below_60": low_confidence_pages,
        "non_assamese_candidate_pages": non_assamese_candidates,
        "duplicate_pages_rejected": duplicate_count,
        "accepted_characters": approximate_character_count,
        "accepted_words": len(words),
        "accepted_token_count": sum(item["token_count"] for item in accepted_rows),
        "tokenizer": tokenizer_info,
        "acceptance_percentage": round(
            100 * len(accepted_rows) / len(records), 2
        )
        if records
        else 0.0,
        "rejection_reason_counts": dict(sorted(reason_counts.items())),
        "filter_thresholds": {
            "minimum_total_letters": MIN_TOTAL_LETTERS,
            "minimum_assamese_unicode_letters": MIN_ASSAMESE_LETTERS,
            "minimum_assamese_share_of_letters": MIN_ASSAMESE_LETTER_RATIO,
            "minimum_mean_ocr_confidence": MIN_OCR_CONFIDENCE,
            "low_confidence_reporting_threshold": LOW_CONFIDENCE_THRESHOLD,
            "maximum_symbol_share": 0.55,
            "language_uncertain_pages_rejected": True,
            "bengali_or_non_assamese_candidates_rejected": True,
            "books_explicitly_marked_bengali_medium_rejected": True,
            "non_assamese_technical_terms": "allowed within Assamese-script pages",
        },
        "automatic_split_status": "created" if splits else "not_created",
        "split_error": split_error,
        "book_split_strategy": (
            f"Deterministic SHA-256 ordering of accepted source-book paths; "
            f"{validation_fraction:.0%} target validation books, at least one book "
            "per split. No book appears in both."
        ),
        "book_distribution": per_book_counts,
        "paths": {
            "accepted_jsonl": str(auto_jsonl),
            "accepted_text": str(auto_txt),
            "rejected_jsonl": str(rejected_jsonl),
            "processed_train_jsonl": str(train_jsonl) if splits else None,
            "processed_validation_jsonl": str(validation_jsonl) if splits else None,
            "processed_train_text": str(train_txt) if splits else None,
            "processed_validation_text": str(validation_txt) if splits else None,
            "split_manifest": str(split_manifest_path) if splits else None,
            "report": str(report_path),
        },
        "warning": (
            "Automatic filtering is heuristic. Accepted OCR can still contain "
            "Assamese spelling errors, wrong words, layout artifacts, Bengali, or "
            "factual errors. It is not human-verified or error-free."
        ),
    }

    accepted_jsonl_text = "".join(
        json.dumps(item, ensure_ascii=False) + "\n" for item in accepted_rows
    )
    rejected_jsonl_text = "".join(
        json.dumps(item, ensure_ascii=False) + "\n" for item in rejected
    )
    accepted_text = "\n\n".join(
        f"[BOOK: {item['book']} | PDF PAGE: {item['page_number']}]\n{item['text']}"
        for item in accepted_rows
    ) + ("\n" if accepted_rows else "")
    outputs = [
        (auto_jsonl, accepted_jsonl_text),
        (auto_txt, accepted_text),
        (rejected_jsonl, rejected_jsonl_text),
    ]
    if splits:
        train_text = "\n\n".join(
            f"[BOOK: {item['book']} | PDF PAGE: {item['page_number']}]\n{item['text']}"
            for item in train_rows
        ) + ("\n" if train_rows else "")
        validation_text = "\n\n".join(
            f"[BOOK: {item['book']} | PDF PAGE: {item['page_number']}]\n{item['text']}"
            for item in validation_rows
        ) + ("\n" if validation_rows else "")
        outputs.extend(
            [
                (
                    train_jsonl,
                    "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in train_rows),
                ),
                (
                    validation_jsonl,
                    "".join(
                        json.dumps(item, ensure_ascii=False) + "\n"
                        for item in validation_rows
                    ),
                ),
                (train_txt, train_text),
                (validation_txt, validation_text),
                (
                    split_manifest_path,
                    json.dumps(
                        {
                            "created_at": created_at,
                            "split_unit": "source book",
                            "dataset_type": report["dataset_type"],
                            "tokenizer": tokenizer_info,
                            "books": per_book_counts,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                    + "\n",
                ),
            ]
        )
    for path, content in outputs:
        _write_new_file(path, content)
    _write_new_file(report_path, _render_report(report))
    return report


def _render_report(report: dict[str, Any]) -> str:
    lines = [
        "# Automatically Filtered Assamese OCR Dataset",
        "",
        f"- Generated: {report['created_at']}",
        "- **Quality status: automatically filtered; not human-reviewed, not error-free, and not guaranteed to be Assamese throughout.**",
        f"- Total OCR pages: {report['total_pages']}",
        f"- Accepted pages: {report['accepted_pages']}",
        f"- Rejected pages: {report['rejected_pages']}",
        f"- Acceptance: {report['acceptance_percentage']}%",
        f"- Empty pages: {report['empty_pages']}",
        f"- Pages with OCR confidence below 60: {report['low_confidence_pages_below_60']}",
        f"- English/Bengali/other non-Assamese candidates: {report['non_assamese_candidate_pages']}",
        f"- Exact duplicate pages rejected: {report['duplicate_pages_rejected']}",
        f"- Accepted characters: {report['accepted_characters']}",
        f"- Accepted words (Unicode word estimate): {report['accepted_words']}",
        f"- Kakugo-tokenizer token count: {report['accepted_token_count']} "
        f"({report['tokenizer']['status']})",
        f"- Review manifest modified: {report['manifest_modified']}",
        "",
        "## Tokenizer",
        "",
        f"- Repository/revision: `{report['tokenizer'].get('tokenizer_repository')}` / "
        f"`{report['tokenizer'].get('tokenizer_revision')}`",
        f"- Local tokenizer class: `{report['tokenizer'].get('tokenizer_class', 'unavailable')}`",
        f"- Vocabulary size: `{report['tokenizer'].get('vocabulary_size', 'unavailable')}`",
        f"- Notes: {report['tokenizer'].get('error') or 'Loaded locally; token counts computed exactly for accepted page text.'}",
        "",
        "## Filter rules and rejection reasons",
        "",
        "| Rejection reason | Pages (overlapping reasons possible) |",
        "|---|---:|",
    ]
    lines.extend(
        f"| `{reason}` | {count} |"
        for reason, count in report["rejection_reason_counts"].items()
    )
    lines.extend(
        [
            "",
            "Counts by rejection reason can overlap. A low-confidence page is reported but is not rejected solely for falling below 60; only scores below the configured 30 threshold are rejected. The script allows Latin technical terms, numbers, equations, and punctuation when the page otherwise passes Assamese-script and quality checks.",
            "",
            "## Source-book split",
            "",
            f"- Status: `{report['automatic_split_status']}`",
            f"- Strategy: {report['book_split_strategy']}",
        ]
    )
    if report["split_error"]:
        lines.append(f"- Split not created: {report['split_error']}")
    lines.extend(
        [
            "",
            "| Book | Split | Accepted pages | Characters | Tokens |",
            "|---|---|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {book['book']} | {book['split']} | {book['accepted_pages']} | "
        f"{book['characters']} | {book['tokens']} |"
        for book in report["book_distribution"]
    )
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            *[f"- `{path}`" for path in report["paths"].values() if path],
            "",
            "## Limitations",
            "",
            report["warning"],
            "OCR confidence is not an accuracy score. Assamese and Bengali share much of their Unicode block; script detection alone cannot distinguish them. Language labels are used as conservative rejection signals, not proof. Raw OCR records and the human-review manifest were not changed.",
            "",
        ]
    )
    return "\n".join(lines)
