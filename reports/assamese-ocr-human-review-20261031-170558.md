# Assamese PDF OCR: Human Review and Pipeline Proposal

Review date: 2026-10-31  
Project: `assamese_chatbot_ai`  
Scope: local inspection, a recorded 15-page OCR sample, and a few exploratory cover/alternate-page checks. No full-corpus OCR, text replacement, training, or remote upload was performed.

## Summary

- Tesseract 5.5.3 is installed at `C:\Program Files\Tesseract-OCR\tesseract.exe`. Its installed language list contains only `asm`; `asm.traineddata` is 2,045,457 bytes. No Assamese language data was downloaded for this test.
- pypdf's raw extraction contains **zero Assamese-block Unicode characters across all 2,559 pages**. This is a useful encoding failure signal, not a language classifier or a count of pages that might become usable after OCR.
- One interior page was OCR-tested in each of 15 Assamese-medium candidates. On the 14 sampled pages that visually contained Assamese, **12 produced mostly readable text with transcription errors**; 2 pages (the Dwiniyat and Sahitya Karani Class VI contents pages) were only partly readable and are not acceptable without manual correction. These are sample-only findings, not counts for all pages in those books.
- The sampled page from `Bigyan_VIII_Part-II_Assamese.pdf` (page 20) is printed in English. Tesseract `asm` returned mostly noise. Another inspected page (page 6) was also English. Verify this book's language/page scope before including it in an Assamese corpus.
- The OCR/visual-review heuristic flagged 2,557/2,559 pages in the preceding report. It is too broad to be treated as an OCR-required count. The current sample shows why per-page human review is necessary.
- Across the recorded runs and small exploratory checks, 23 distinct PDF pages were rendered/OCR-tested (less than 1% of the 2,559-page set). The linked final report contains the fixed 15-page comparison; the other checks were diagnostic only.
- No OCR text has been added to or used to replace files under `data\extracted_text\`. **The number of usable Assamese pages in the full 2,559-page set remains unknown** until approved, page-by-page processing and review.

## Tesseract comparison

Rendered page images locally using pypdfium2 at 300 DPI. Compared Tesseract LSTM with Assamese data (`--oem 1`, `-l asm`) and page segmentation modes (PSM) 3, 6, and 11. All 15 rendered page images and exact OCR outputs are in the [timestamped sample report](./assamese-ocr-sample-20261031-170558.md), [JSON results](./assamese-ocr-sample-20261031-170558.json), and [sample image directory](./ocr-sample-20261031-170558).

Human review of the rendered images and corresponding outputs:

- **PSM 3** was the most consistent starting point for full-page Assamese paragraphs and mixed page layouts. It produced mostly readable text on 12 of the 14 sampled Assamese pages, but introduced spelling, punctuation, and occasional word errors.
- **PSM 6** was comparable on dense, single-column pages and recovered more of the Dwiniyat contents sample than PSM 3. It was not consistently better across the other pages.
- **PSM 11** often returned more characters, but also recognized decorative marks and page artwork as text. It is not recommended as the default.
- For the 15 final pages, mean OCR times were **2.22 s/page for PSM 3**, **2.05 s/page for PSM 6**, and **2.34 s/page for PSM 11**. These are local CPU measurements on this particular sample, not a full-run estimate.
- Assamese and Bengali share much of their Unicode block. Script-character counts alone cannot validate Assamese recognition. The 12/14 readability assessment is based on visual comparison with the page images; it is not a word-error-rate benchmark and does not mean the text is ready for training.

## Per-PDF findings

All rows below describe the selected page only. "Readable with correction" means the OCR is visibly legible but still needs proofreading; it does not mean the entire PDF was validated.

| PDF | Sample finding | Suggested route |
|---|---|---|
| `Ami Aru Amar Paribesh_Class V_Assamese.pdf` | Page 6's native text is only the copyright footer. PSM 3 reads the page's Assamese foreword; some word errors remain. | OCR image/text pages; proofread. |
| `Ankuran (Pancham Bhag) (Language (L1))_Class 5_Assamese medium.pdf` | Page 6 is footer-only natively. PSM 3/6/11 produce mostly readable Assamese on the page. | OCR; proofread. |
| `Ankuran (Saptam Bhag) (Language (L1))_Class 7_Assamese medium.pdf` | Page 7 has thousands of extracted characters but no Assamese Unicode; the output is visibly font-mapped garbage. OCR recovers readable text. | Broken character mapping; use OCR unless a verified font map can be recovered. |
| `Ankuran (Sastha Bhag) (Language (L1))_Class 6_Assamese medium.pdf` | Page 6 is footer-only natively. OCR reads the Assamese contributor list, with name/term errors. | OCR; carefully proofread names. |
| `Assamese.pdf` | Page 7 has no native text. OCR produces several readable Assamese paragraphs; the illustration at the bottom causes extra text in PSM 11. | Scanned page; OCR PSM 3/6, review. |
| `Bigyan (C) (With keywords in English) (Science)_Class 7_Assamese medium.pdf` | Page 6's pypdf text is font-mapped and has no Assamese Unicode. OCR reads the Assamese foreword; embedded English terms need review. | Broken character mapping; OCR and preserve technical terms. |
| `Bigyan_VIII_Part-II_Assamese.pdf` | Sampled pages 6 and 20 are English-language print; the `asm` OCR output is noise. This does not establish the language of every page in this PDF. Page 6's earlier OCR run is in the [prior sample report](./assamese-ocr-sample-20261031-165306.md). | Verify language/page scope; do not treat these OCR outputs as Assamese. |
| `Dwiniyat (Old) (R)(Dwiniyat)_Class 7_Assamese medium.pdf` | Page 6 is a low-resolution contents page. PSM 3 mostly returns page numbers; PSM 6 recovers some headings but with errors. | OCR candidate; manual transcription/review required. |
| `Sahitya Karani (Pratham Bhag) (L3 (Assamese))_Class 6.pdf` | Page 6 is a contents page. All modes add noise; PSM 11 recovers some headings but is incomplete. | OCR candidate; this sample is not usable without manual correction. |
| `Sahitya Karani (Tritiya Bhag) (L3 (Assamese))_Class 8.pdf` | Page 7's native output is garbled despite thousands of characters. OCR produces readable Assamese text with minor recognition errors. | Broken character mapping; OCR and proofread. |
| `Samaj Bichitra_Class VI_Textbook_Assamese.pdf` | Page 24's native output is font-mapped. OCR reads the Assamese explanation, but symbols/numerals and terminology need review. | Broken character mapping; OCR and preserve mathematical notation. |
| `Samaj Bigyan (Dwitiya Bhag) (Social Science)_Class 7_Assamese medium.pdf` | Page 6 is footer-only natively. OCR reads the Assamese foreword with minor errors. | OCR; proofread. |
| `Science_Class VI_Part 1_Assamese.pdf` | Page 250's native text is font-mapped. OCR reads the Assamese contributor text; this sample is not a science-content accuracy test. | Broken character mapping; OCR and inspect science pages separately. |
| `Spandan-Part I-ClassIII-Assamese(L1).pdf` | Page 6 is footer-only natively. OCR reads the Assamese foreword, with some recognition errors. | OCR; proofread. |
| `Unmesh I-Class VI-Assamese.pdf` | Page 7 contains thousands of unusable native characters. OCR recovers readable Assamese text with some spelling errors. | Broken character mapping; OCR and proofread. |

Two other PDFs in the source directory are explicitly Arabic (L4) and Bengali-medium; they were not treated as Assamese training candidates or included in this OCR sample.

## Font and native-extraction investigation

- The sampled high-text failures are not solved by switching from pypdf to PDFium: PDFium returned the same non-Assamese code-point sequences on eight checked suspect pages.
- Several suspect pages use subsetted Geetanjali fonts with `/ToUnicode` maps present. Their visible Assamese text and extracted Latin/extended-symbol output disagree, so the presence of a map does not prove that the map is correct. The affected examples include `Ankuran (Saptam Bhag)`, `Bigyan (C)`, `Sahitya Karani (Tritiya Bhag)`, `Samaj Bichitra`, `Science_Class VI`, and `Unmesh`.
- pypdf also reported a CFF/Type1 parsing warning because fontTools was absent. Installing fontTools for a local test removed that warning but left the sampled page text unchanged (still zero Assamese-block characters). It is therefore not a sufficient correction by itself and is not added as a project dependency.
- For those documents, a true font correction would require validating the embedded font's glyph-to-Unicode mapping against page images, not substituting guessed character maps. OCR is the more practical fallback in the current evidence.

## Proposed conservative correction pipeline

1. Keep the original PDFs and existing raw extraction immutable. Write OCR into a separate per-book/per-page candidate output with source hash, page number, renderer, DPI, Tesseract version, language, OEM, PSM, and confidence/word metadata.
2. Triage each page using native text quality and visual inspection. Do not mark OCR required merely because a page has any image object: decorative images and small figures are common.
3. If native text is valid Unicode and visually matches the page, retain it. If the PDF has garbled custom-font mapping, try font-map correction only where the actual embedded mapping can be demonstrated; otherwise route that page to OCR.
4. For Assamese image pages, render at 300 DPI and use local Tesseract `asm`, PSM 3 as the initial full-page setting. Compare PSM 6 on structured/single-column pages. Avoid automatically accepting PSM 11.
5. Preserve raw extraction, OCR candidate, and any human-corrected text as distinct versions. Never silently replace text, remove page content, or use OCR script counts as an acceptance threshold.
6. Require page-by-page human review against the rendered PDF image. Track accepted, corrected, uncertain, and unreadable pages; only later build a corpus from explicitly approved pages, after textbook rights have been reviewed.

## Commands

Install the project's declared dependencies and run the fixed sample:

```powershell
Set-Location "$HOME\Downloads\assamese_chatbot_ai"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.evaluate_assamese_ocr_samples
```

The evaluation script is deliberately fixed to a 15-page sample. It does not expose a full-book/all-pages mode. **Wait for explicit approval before implementing or running OCR over the remaining pages.**
