# Assamese Textbook OCR Run

- Generated: 2026-10-31T20:24:19+05:30
- Scope: all PDF pages
- PDFs discovered: 17
- Total pages inventoried: 2559
- Pages selected for this run: 2559
- Pages newly processed: 2509
- Previously completed pages reused: 50
- Failed selected pages: 0
- Pages not included in this pilot: 0
- Sum of page OCR processing times (including reused pages): 10001.984 seconds
- This invocation elapsed time (includes inventory/reporting and cached language checks): 9905.039 seconds
- Peak RSS during page OCR: 1310986240 bytes
- Peak RSS including local classifier loading/checks: 1310986240 bytes
- RSS after classifier load: 1216458752 bytes
- Memory measurement: Peak RSS is sampled for the Python OCR runner and its live child processes; brief peaks between 100 ms samples can be missed.
- Tesseract: `tesseract v5.5.3.20260724`; languages: `asm`
- Local language classifier available: True (cache-only; no model download)
- OCR settings: pypdfium2 at 300 DPI; Tesseract `asm`, OEM 1, PSM 3; timeout 120 s; maximum attempts 2
- OCR output is saved separately under `data/ocr_text/`; original PDFs and raw extraction outputs are not changed.
- Every OCR page is flagged for human review; confidence and language/script heuristics are not proof of correctness.

## Per-book summary

| PDF | Pages in book | Selected | Completed | Failed | Mean confidence | Review flags | Report |
|---|---:|---:|---:|---:|---:|---|---|
| Adrasul Arabia (Old) (Arabic (L4))_Class 8_Assamese medium.pdf | 87 | 87 | 87 | 0 | 45.53 | empty_ocr: 8, human_review_required: 87, language_uncertain: 1, low_confidence: 67, no_assamese_block_text_candidate: 1 | [open](books/Adrasul%20Arabia%20%28Old%29%20%28Arabic%20%28L4%29%29_Class%208_Assamese%20medium.md) |
| Ami Aru Amar Paribesh_Class V_Assamese.pdf | 144 | 144 | 144 | 0 | 85.77 | empty_ocr: 1, human_review_required: 144, low_confidence: 2 | [open](books/Ami%20Aru%20Amar%20Paribesh_Class%20V_Assamese.md) |
| Ankuran (Pancham Bhag) (Language (L1))_Class 5_Assamese medium.pdf | 143 | 143 | 143 | 0 | 85.06 | human_review_required: 143, low_confidence: 2 | [open](books/Ankuran%20%28Pancham%20Bhag%29%20%28Language%20%28L1%29%29_Class%205_Assamese%20medium.md) |
| Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf | 147 | 147 | 147 | 0 | 85.11 | empty_ocr: 1, human_review_required: 147, low_confidence: 6 | [open](books/Ankuran%20%28Saptam%20Bhag%29%20%28Language%20%28L1%29%29_Class%207_Assamese%20medium.md) |
| Ankuran (Sastha Bhag) (Language (L1))_Class 6_Assamese medium.pdf | 148 | 148 | 148 | 0 | 86.63 | empty_ocr: 1, human_review_required: 148, low_confidence: 5 | [open](books/Ankuran%20%28Sastha%20Bhag%29%20%28Language%20%28L1%29%29_Class%206_Assamese%20medium.md) |
| Assamese.pdf | 118 | 118 | 118 | 0 | 80.87 | english_only_candidate: 15, human_review_required: 118, language_uncertain: 15, low_confidence: 20 | [open](books/Assamese.md) |
| Bigyan (C) (With keywords in English) (Science)_Class 7_Assamese medium.pdf | 248 | 248 | 248 | 0 | 83.42 | empty_ocr: 1, human_review_required: 248, low_confidence: 2 | [open](books/Bigyan%20%28C%29%20%28With%20keywords%20in%20English%29%20%28Science%29_Class%207_Assamese%20medium.md) |
| Bigyan_VIII_Part-II_Assamese.pdf | 286 | 286 | 286 | 0 | 62.9 | english_only_candidate: 125, human_review_required: 286, language_uncertain: 143, low_confidence: 149 | [open](books/Bigyan_VIII_Part-II_Assamese.md) |
| Dwiniyat (Old) (R) (Dwiniyat)_Class 7_Bengali medium.pdf | 30 | 30 | 30 | 0 | 80.39 | bengali_or_non_assamese_candidate: 27, empty_ocr: 1, human_review_required: 30, language_uncertain: 1, low_confidence: 2 | [open](books/Dwiniyat%20%28Old%29%20%28R%29%20%28Dwiniyat%29_Class%207_Bengali%20medium.md) |
| Dwiniyat (Old) (R)(Dwiniyat)_Class 7_Assamese medium.pdf | 68 | 68 | 68 | 0 | 77.27 | bengali_or_non_assamese_candidate: 1, empty_ocr: 4, human_review_required: 68, low_confidence: 10 | [open](books/Dwiniyat%20%28Old%29%20%28R%29%28Dwiniyat%29_Class%207_Assamese%20medium.md) |
| Sahitya Karani (Pratham Bhag) (L3 (Assamese))_Class 6.pdf | 116 | 116 | 116 | 0 | 80.61 | empty_ocr: 3, human_review_required: 116, low_confidence: 5 | [open](books/Sahitya%20Karani%20%28Pratham%20Bhag%29%20%28L3%20%28Assamese%29%29_Class%206.md) |
| Sahitya Karani (Tritiya Bhag) (L3 (Assamese))_Class 8.pdf | 100 | 100 | 100 | 0 | 85.64 | empty_ocr: 3, human_review_required: 100, low_confidence: 1 | [open](books/Sahitya%20Karani%20%28Tritiya%20Bhag%29%20%28L3%20%28Assamese%29%29_Class%208.md) |
| Samaj Bichitra_Class VI_Textbook_Assamese.pdf | 144 | 144 | 144 | 0 | 85.62 | empty_ocr: 1, human_review_required: 144, low_confidence: 4 | [open](books/Samaj%20Bichitra_Class%20VI_Textbook_Assamese.md) |
| Samaj Bigyan (Dwitiya Bhag) (Social Science)_Class 7_Assamese medium.pdf | 224 | 224 | 224 | 0 | 87.1 | human_review_required: 224, low_confidence: 6 | [open](books/Samaj%20Bigyan%20%28Dwitiya%20Bhag%29%20%28Social%20Science%29_Class%207_Assamese%20medium.md) |
| Science_Class VI_Part 1_Assamese.pdf | 252 | 252 | 252 | 0 | 64.45 | english_only_candidate: 115, human_review_required: 252, language_uncertain: 119, low_confidence: 125 | [open](books/Science_Class%20VI_Part%201_Assamese.md) |
| Spandan-Part I-ClassIII-Assamese(L1).pdf | 152 | 152 | 152 | 0 | 76.65 | human_review_required: 152, low_confidence: 13 | [open](books/Spandan-Part%20I-ClassIII-Assamese%28L1%29.md) |
| Unmesh I-Class VI-Assamese.pdf | 152 | 152 | 152 | 0 | 84.22 | human_review_required: 152, low_confidence: 2 | [open](books/Unmesh%20I-Class%20VI-Assamese.md) |

## Review notes

- `english_only_candidate` uses the cached local IndicLID top label when available, with a Latin-letter fallback. It is a review flag, not proof that a page is English. Bengali and Assamese share much of their Unicode block; the classifier output is also not a correctness guarantee.
- `low_confidence` means mean Tesseract word confidence below 60; confidence is not a calibrated probability of correctness.
- Empty, script-mismatch, and suspicious-text pages are reported, not silently discarded. Inspect their page image and raw OCR.
- The pilot intentionally does not process pages outside its selected sample. Use `--all-pages` only after explicit approval.
