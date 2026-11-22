# Automatically Filtered Assamese OCR Dataset

- Generated: 2026-11-01T05:42:51+05:30
- **Quality status: automatically filtered; not human-reviewed, not error-free, and not guaranteed to be Assamese throughout.**
- Total OCR pages: 2559
- Accepted pages: 2057
- Rejected pages: 502
- Acceptance: 80.38%
- Empty pages: 24
- Pages with OCR confidence below 60: 421
- English/Bengali/other non-Assamese candidates: 307
- Exact duplicate pages rejected: 3
- Accepted characters: 2686616
- Accepted words (Unicode word estimate): 917199
- Kakugo-tokenizer token count: 3657160 (exact)
- Review manifest modified: False

## Tokenizer

- Repository/revision: `ptrdvn/kakugo-3B-asm` / `a6a854a0a680c4c57ec026df014f8f5964da8721`
- Local tokenizer class: `GPT2Tokenizer`
- Vocabulary size: `100352`
- Notes: Counted with Transformers `AutoTokenizer`, which loads the repository-declared `GPT2Tokenizer`; this is also the tokenizer-loading path used by the training script. A direct `tokenizers.Tokenizer` load of `tokenizer.json` counted 3,374,540 tokens for the same text, so that differing backend is not used as an exact-count fallback. Without Transformers, the corpus builder now labels its character-based count as approximate.

## Filter rules and rejection reasons

| Rejection reason | Pages (overlapping reasons possible) |
|---|---:|
| `bengali_or_non_assamese_candidate` | 28 |
| `duplicate_page` | 3 |
| `empty_page` | 24 |
| `english_only_candidate` | 205 |
| `insufficient_assamese_script` | 292 |
| `non_assamese_medium_book` | 30 |
| `other_non_assamese_language` | 212 |
| `repeated_ocr_artifact` | 39 |
| `too_short` | 422 |
| `uncertain_language` | 279 |
| `very_low_ocr_confidence` | 32 |

Counts by rejection reason can overlap. A low-confidence page is reported but is not rejected solely for falling below 60; only scores below the configured 30 threshold are rejected. The script allows Latin technical terms, numbers, equations, and punctuation when the page otherwise passes Assamese-script and quality checks.

## Source-book split

- Status: `created`
- Strategy: Deterministic SHA-256 ordering of accepted source-book paths; 20% target validation books, at least one book per split. No book appears in both.

| Book | Split | Accepted pages | Characters | Tokens |
|---|---|---:|---:|---:|
| Adrasul Arabia (Old) (Arabic (L4))_Class 8_Assamese medium.pdf | train | 37 | 22144 | 25184 |
| Ami Aru Amar Paribesh_Class V_Assamese.pdf | validation | 135 | 178090 | 249289 |
| Ankuran (Pancham Bhag) (Language (L1))_Class 5_Assamese medium.pdf | train | 137 | 126547 | 168847 |
| Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf | train | 142 | 167389 | 227881 |
| Ankuran (Sastha Bhag) (Language (L1))_Class 6_Assamese medium.pdf | train | 135 | 145220 | 200976 |
| Assamese.pdf | train | 103 | 186680 | 266167 |
| Bigyan (C) (With keywords in English) (Science)_Class 7_Assamese medium.pdf | train | 242 | 430320 | 555067 |
| Bigyan_VIII_Part-II_Assamese.pdf | train | 139 | 205011 | 277847 |
| Dwiniyat (Old) (R)(Dwiniyat)_Class 7_Assamese medium.pdf | train | 61 | 68682 | 94702 |
| Sahitya Karani (Pratham Bhag) (L3 (Assamese))_Class 6.pdf | train | 77 | 44725 | 58144 |
| Sahitya Karani (Tritiya Bhag) (L3 (Assamese))_Class 8.pdf | train | 83 | 66295 | 88619 |
| Samaj Bichitra_Class VI_Textbook_Assamese.pdf | validation | 136 | 204053 | 283186 |
| Samaj Bigyan (Dwitiya Bhag) (Social Science)_Class 7_Assamese medium.pdf | train | 221 | 401018 | 566404 |
| Science_Class VI_Part 1_Assamese.pdf | train | 130 | 150917 | 206603 |
| Spandan-Part I-ClassIII-Assamese(L1).pdf | validation | 131 | 131228 | 171443 |
| Unmesh I-Class VI-Assamese.pdf | train | 148 | 158297 | 216801 |

## Outputs

- `data\training_data\auto_filtered_assamese.jsonl`
- `data\training_data\auto_filtered_assamese.txt`
- `data\training_data\auto_rejected_pages.jsonl`
- `data\training_data\processed\train.jsonl`
- `data\training_data\processed\validation.jsonl`
- `data\training_data\processed\train.txt`
- `data\training_data\processed\validation.txt`
- `data\training_data\processed\split-manifest.json`
- `reports\automatic-corpus-quality-report.md`

## Limitations

Automatic filtering is heuristic. Accepted OCR can still contain Assamese spelling errors, wrong words, layout artifacts, Bengali, or factual errors. It is not human-verified or error-free.
OCR confidence is not an accuracy score. Assamese and Bengali share much of their Unicode block; script detection alone cannot distinguish them. Language labels are used as conservative rejection signals, not proof. Raw OCR records and the human-review manifest were not changed.
