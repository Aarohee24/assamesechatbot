from __future__ import annotations

from collections import Counter
import getpass
from pathlib import Path
import sys
from typing import Any

import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.ocr_review import OCRReviewStore


st.set_page_config(page_title="অসমীয়া OCR মানৱ পৰ্যালোচনা", layout="wide")
st.title("অসমীয়া পাঠ্যপুথিৰ OCR পৰ্যালোচনা")
st.caption("প্ৰতিটো পৃষ্ঠা মূল PDF-ৰ সৈতে মিলাই নিজে পৰীক্ষা কৰক।")
st.warning(
    "OCR confidence বা ভাষা-শ্ৰেণীবিভাজনে পৃষ্ঠাটো শুদ্ধ বুলি প্ৰমাণ নকৰে। "
    "অনুমোদনৰ আগতে সম্পূৰ্ণ পাঠটো মূল পৃষ্ঠাৰ সৈতে তুলনা কৰক।"
)

try:
    store = OCRReviewStore()
except (FileNotFoundError, RuntimeError, ValueError) as error:
    st.error(f"পৰ্যালোচনা তথ্য লোড কৰিব পৰা নগ'ল: {error}")
    st.stop()

status_counts = Counter(page["review_status"] for page in store.pages)
reviewed_count = len(store.pages) - status_counts["pending"]
metric_columns = st.columns(6)
metric_columns[0].metric("মুঠ পৃষ্ঠা", len(store.pages))
metric_columns[1].metric("পৰ্যালোচনা কৰা", reviewed_count)
metric_columns[2].metric("অনুমোদিত", status_counts["approved"])
metric_columns[3].metric("প্ৰত্যাখ্যাত", status_counts["excluded"])
metric_columns[4].metric("সংশোধন প্ৰয়োজন", status_counts["needs_correction"])
metric_columns[5].metric("বাকী", status_counts["pending"])
st.progress(reviewed_count / len(store.pages) if store.pages else 0.0)

flag_labels = {
    "low_confidence": "কম confidence",
    "english_only_candidate": "ইংৰাজী সম্ভাৱনা",
    "bengali_or_non_assamese_candidate": "বাংলা/অন্য ভাষাৰ সম্ভাৱনা",
    "language_uncertain": "ভাষা অনিশ্চিত",
}

with st.sidebar:
    st.header("পৃষ্ঠাৰ বাছনি")
    chosen_flags = st.multiselect(
        "পতাকা অনুসৰি ফিল্টাৰ কৰক",
        options=list(flag_labels),
        format_func=lambda flag: flag_labels[flag],
    )
    status_filter = st.multiselect(
        "পৰ্যালোচনা অৱস্থা",
        options=["pending", "needs_correction", "approved", "excluded"],
        default=["pending", "needs_correction"],
        format_func=lambda status: {
            "pending": "বাকী",
            "needs_correction": "সংশোধন প্ৰয়োজন",
            "approved": "অনুমোদিত",
            "excluded": "প্ৰত্যাখ্যাত",
        }[status],
    )
    sort_by = st.selectbox(
        "সজোৱা",
        options=[
            "Flagged first",
            "Lowest confidence",
            "English candidates",
            "Bengali candidates",
            "Uncertain language",
            "Book and page",
        ],
        format_func=lambda option: {
            "Flagged first": "আগতে পতাকাযুক্ত",
            "Lowest confidence": "আটাইতকৈ কম confidence",
            "English candidates": "ইংৰাজী সম্ভাৱনা আগতে",
            "Bengali candidates": "বাংলা সম্ভাৱনা আগতে",
            "Uncertain language": "অনিশ্চিত ভাষা আগতে",
            "Book and page": "কিতাপ আৰু পৃষ্ঠা",
        }[option],
    )

filtered_pages: list[dict[str, Any]] = []
record_by_key = {}
for page in store.pages:
    if page["review_status"] not in status_filter:
        continue
    record = store.ocr_record(page)
    flags = set(record.get("review_flags", []))
    if chosen_flags and not flags.intersection(chosen_flags):
        continue
    key = (
        page["source_relative_path"],
        page["source_pdf_sha256"],
        int(page["page_number"]),
    )
    record_by_key[key] = record
    filtered_pages.append(page)


def _record(page: dict[str, Any]) -> dict[str, Any]:
    key = (
        page["source_relative_path"],
        page["source_pdf_sha256"],
        int(page["page_number"]),
    )
    return record_by_key[key]


def _confidence(page: dict[str, Any]) -> float:
    value = _record(page).get("confidence", {}).get("mean")
    return float(value) if isinstance(value, (int, float)) else -1.0


sort_flags = {
    "English candidates": "english_only_candidate",
    "Bengali candidates": "bengali_or_non_assamese_candidate",
    "Uncertain language": "language_uncertain",
}
if sort_by == "Lowest confidence":
    filtered_pages.sort(key=lambda page: (_confidence(page) < 0, _confidence(page)))
elif sort_by in sort_flags:
    target_flag = sort_flags[sort_by]
    filtered_pages.sort(
        key=lambda page: (
            target_flag not in _record(page).get("review_flags", []),
            _confidence(page) if _confidence(page) >= 0 else 101.0,
            page["book"],
            page["page_number"],
        )
    )
elif sort_by == "Book and page":
    filtered_pages.sort(key=lambda page: (page["book"], page["page_number"]))
else:
    filtered_pages.sort(
        key=lambda page: (
            not (
                set(_record(page).get("review_flags", []))
                - {"human_review_required"}
            ),
            _confidence(page) if _confidence(page) >= 0 else 101.0,
            page["book"],
            page["page_number"],
        )
    )

if not filtered_pages:
    st.info("এই ফিল্টাৰত কোনো পৃষ্ঠা নাই। ফিল্টাৰ বা অৱস্থা সলনি কৰক।")
    st.stop()

def _page_label(page: dict[str, Any]) -> str:
    record = _record(page)
    confidence = record.get("confidence", {}).get("mean")
    confidence_label = f"{confidence:.1f}" if isinstance(confidence, (int, float)) else "N/A"
    return (
        f"{page['book']} | পৃষ্ঠা {page['page_number']} | "
        f"confidence {confidence_label} | {page['review_status']}"
    )


page_keys = [
    (page["source_relative_path"], page["source_pdf_sha256"], int(page["page_number"]))
    for page in filtered_pages
]
page_by_key = {
    (page["source_relative_path"], page["source_pdf_sha256"], int(page["page_number"])): page
    for page in filtered_pages
}
selected_key = st.selectbox(
    "পৰ্যালোচনাৰ বাবে পৃষ্ঠা",
    options=page_keys,
    format_func=lambda key: _page_label(page_by_key[key]),
)
page = page_by_key[selected_key]
record = _record(page)
confidence = record.get("confidence", {})
language = record.get("language_identification", {})

st.subheader(f"{page['book']} — PDF পৃষ্ঠা {page['page_number']}")
metadata_columns = st.columns(3)
metadata_columns[0].write(f"**OCR confidence:** {confidence.get('mean', 'N/A')}")
metadata_columns[1].write(
    f"**ভাষা পৰীক্ষা:** {language.get('label', 'N/A')} "
    f"({language.get('confidence', 'N/A')})"
)
metadata_columns[2].write(
    "**Review flags:** "
    + (", ".join(record.get("review_flags", [])) or "কোনো অতিৰিক্ত পতাকা নাই")
)

image_column, text_column = st.columns([1, 1])
with image_column:
    with st.spinner("মূল PDF পৃষ্ঠা ৰেণ্ডাৰ কৰা হৈছে..."):
        try:
            page_image = store.render_pdf_page(page)
        except (FileNotFoundError, RuntimeError, ValueError, OSError) as error:
            st.error(f"মূল PDF পৃষ্ঠা দেখুৱাব পৰা নগ'ল: {error}")
            st.stop()
    st.image(page_image, caption=f"মূল PDF — পৃষ্ঠা {page['page_number']}", use_container_width=True)
    page_image.close()

raw_text = record.get("text", "")
current_text = store.reviewed_text(page)
with text_column:
    st.text_area("মূল OCR (পৰিৱৰ্তন নকৰা)", raw_text, height=230, disabled=True)
    with st.form(key=f"review-{page['source_pdf_sha256']}-{page['page_number']}"):
        corrected_text = st.text_area(
            "সংশোধিত Assamese পাঠ",
            value=current_text,
            height=330,
            help="OCR-ৰ অৰ্থ সলনি নকৰাকৈ মূল পৃষ্ঠাৰ সৈতে মিলাই ভুলবোৰ সংশোধন কৰক।",
        )
        reviewer = st.text_input("পৰ্যালোচকৰ নাম", value=getpass.getuser())
        notes = st.text_area("টোকা", value=page.get("review_notes", ""), height=80)
        action_columns = st.columns(3)
        approve = action_columns[0].form_submit_button("Approve", type="primary")
        reject = action_columns[1].form_submit_button("Reject")
        needs_correction = action_columns[2].form_submit_button("Needs Correction")

    action_status = None
    if approve:
        action_status = "approved"
    elif reject:
        action_status = "excluded"
    elif needs_correction:
        action_status = "needs_correction"
    if action_status:
        try:
            store.update_review(
                page,
                status=action_status,
                reviewer=reviewer,
                notes=notes,
                corrected_text=corrected_text,
            )
        except (OSError, RuntimeError, ValueError) as error:
            st.error(f"পৰ্যালোচনা সংৰক্ষণ কৰিব পৰা নগ'ল: {error}")
        else:
            st.success("পৰ্যালোচনা আৰু অগ্ৰগতি তৎক্ষণাৎ সংৰক্ষণ কৰা হৈছে।")
            st.rerun()

st.caption(
    "সংশোধিত পাঠ raw OCR-ৰ পৰা পৃথককৈ সংৰক্ষিত হয়। "
    "মাত্ৰ স্পষ্টভাৱে অনুমোদিত পৃষ্ঠাহে পৰৱৰ্তী corpus-ত অন্তৰ্ভুক্ত হ'ব।"
)
