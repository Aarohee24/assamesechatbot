# Kakugo Model Training Feasibility Audit

Audit date: 2026-10-31  
Project model: `trubits/kakugo-3b-asm:q4_k_m` in Ollama 0.40.13  
Scope: Phases 1 and 2 only. No model weights were downloaded; no model was modified or trained.

## Findings

### Installed model and upstream checkpoint

- `ollama show` reports architecture `granite`, 3.4B parameters, Q4_K_M quantization, a 131,072 context length, and 2,560 embedding width.
- `ollama show --modelfile` identifies the installed artifact only as a local GGUF blob and shows a `{{ .Prompt }}` template and Granite stop tokens. That local metadata does **not** prove which exact upstream checkpoint or revision was converted into this blob.
- The public [Kakugo 3B Assamese model card](https://huggingface.co/ptrdvn/kakugo-3B-asm) identifies the model as an Assamese fine-tune of [IBM Granite 4.0 Micro](https://huggingface.co/ibm-granite/granite-4.0-micro). Hugging Face model metadata lists `safetensors`, Apache-2.0, and the Granite base. The model card says it was fine-tuned for one epoch using LlamaFactory.
- A trainable Hugging Face-format Kakugo checkpoint is available, so training need not use the Ollama GGUF. The public file listing totals **6,805,711,176 bytes (about 6.34 GiB)** for two BF16 safetensors shards. This size was read from repository metadata; the shards were **not downloaded**.
- The upstream checkpoint is a credible candidate for the intended model, but its exact weight identity relative to the installed `trubits/...:q4_k_m` GGUF remains unverified. Before training, preserve the current Ollama model as the baseline and explicitly select the upstream checkpoint/revision.

### Architecture, tokenizer, and context

The upstream checkpoint `config.json` reports:

| Property | Value |
|---|---|
| Transformers class | `GraniteMoeHybridForCausalLM` |
| `model_type` | `granitemoehybrid` |
| Hidden width | 2,560 |
| Layers | 40 (the published config lists attention for all 40 layer types) |
| Attention heads / KV heads | 40 / 8 |
| Vocabulary size | 100,352 |
| Maximum positions | 131,072 |
| Published checkpoint dtype | BF16 |

The Kakugo and IBM base repositories have identical SHA-1 object identifiers and byte sizes for `tokenizer.json` (7,153,421 bytes), `vocab.json` (1,612,704 bytes), and `merges.txt` (916,646 bytes). The Kakugo tokenizer config names `GPT2Tokenizer`; the model config is the reliable source for the vocabulary/context values. Tokenizer metadata's `model_max_length` is a very large sentinel rather than the actual limit, so use `max_position_embeddings=131072`. The Kakugo repo has a separate `chat_template.jinja`; Ollama's installed local Modelfile reports `{{ .Prompt }}`. They are not assumed to be interchangeable.

IBM's [Transformers GraniteMoeHybrid documentation](https://huggingface.co/docs/transformers/main/en/model_doc/granitemoehybrid) documents causal-LM training support. The Kakugo card supplies a Transformers/LlamaFactory training recipe. This is strong evidence that the upstream safetensors checkpoint is trainable with a compatible Transformers stack, subject to pinning a version that supports this architecture (the published config was produced with Transformers 4.57.1 and calls for `trust_remote_code: true`).

### Training methods

- **Continued pretraining:** conceptually compatible with a causal LM: tokenize textbook text with the exact Granite tokenizer and train next-token loss on the trainable checkpoint. The Kakugo authors' published run is SFT, not continued pretraining; their documented recipe does not validate textbook continued pretraining or its hyperparameters.
- **Full fine-tuning reference:** the Kakugo model card's LlamaFactory recipe uses BF16, sequence length 8,000, batch size 1, and DeepSpeed ZeRO-3. The Kakugo project README says its successful run used **8 RTX 3090 GPUs**. This is the only concrete hardware reference found for the upstream recipe.
- **LoRA:** technically plausible because PEFT can attach low-rank updates to supported linear layers while freezing base weights. However, the Kakugo training recipe uses full fine-tuning and does not document a LoRA run. The precise target module names, save/merge path, and continued-pretraining behavior have not been tested for this checkpoint. A small disposable GPU compatibility test is required before committing to it.
- **QLoRA:** not verified for this checkpoint/runtime. It adds quantization/kernel compatibility constraints on top of LoRA; it should not be assumed to work on Windows CPU.
- Adapter continued pretraining updates only adapter parameters, not the original base weights. It can reduce memory, but it may have less capacity to absorb broad textbook terminology and facts than full-model continued pretraining; it is not equivalent to updating every base weight.

### License and training-data rights

The Kakugo model card declares **Apache-2.0**, and the IBM Granite base is also listed as Apache-2.0. Preserve the relevant notices and check the upstream repositories before redistribution. This does not grant rights to the textbooks: their publisher/licensing status must be reviewed before any training run or sharing of extracted text/checkpoints.

### Hardware feasibility

- This host reports **7.68 GiB total physical RAM** through Windows, not 16 GiB. A hardware recheck on 2026-10-31 found an Intel Core i5-12450H (8 cores/12 threads), NVIDIA GTX 1650 with 4 GiB VRAM (compute capability 7.5), Intel UHD graphics, and about 111 GiB free on C:. The project environment has no PyTorch installation. The GTX 1650 does not support BF16 arithmetic.
- BF16 model weights alone occupy about 6.34 GiB before activations, gradients, optimizer state, tokenizer, Windows, and work buffers. A raw full-training state estimate for 3.40B parameters is about 38 GiB with BF16 weights/gradients and FP32 Adam moments, or ~51 GiB with an additional FP32 master copy, before activations and workspaces. This host cannot hold the full checkpoint plus training state on CPU or its 4-GiB GPU; do not attempt training here.
- The upstream published full-SFT recipe used 8 × 24-GiB RTX 3090 GPUs and ZeRO-3 at sequence length 8,000. Treat this as a reproducibility reference, not a proven minimum for continued pretraining. Plan for at least 64 GiB on a single GPU for an unsharded full-parameter attempt, or the upstream 8 × 24-GiB distributed setup; exact needs must be established by a disposable GPU memory test.
- LoRA targets and PEFT support have not been tested for this Granite/Mamba hybrid model. A 24-GiB BF16 card is only a possible LoRA test starting point, not a verified requirement. QLoRA is not approved/verified for this architecture and Windows environment. Do not assume either is supported.
- A GPU run needs local storage for the 6.34-GiB BF16 checkpoint plus optimizer state, checkpoints, and exports. About 111 GiB is currently free locally, but this does not address the missing training hardware. No paid cloud service will be selected or used without explicit approval. Do not upload textbook PDFs to a cloud GPU.

### OCR investigation

The current environment has Tesseract 5.5.3 installed at `C:\Program Files\Tesseract-OCR\tesseract.exe` with Assamese `asm.traineddata` (2,045,457 bytes); the only installed language is `asm`. pypdfium2 is declared as a local PDF rasterizer. A 15-page OCR comparison across the Assamese-medium candidates has now been run at 300 DPI with Tesseract LSTM and PSM 3, 6, and 11. The human-reviewed findings and proposed pipeline are in [reports/assamese-ocr-human-review-20261031-170558.md](./assamese-ocr-human-review-20261031-170558.md); exact outputs and page images are linked there.

On the 14 sampled pages visually containing Assamese, 12 produced mostly readable OCR that still needs proofreading, while two contents pages were only partially recognized. A selected page from `Bigyan_VIII_Part-II_Assamese.pdf` was English and its Assamese OCR output was noise; the book's page-language scope needs checking. PSM 3 was the most consistent full-page starting point, PSM 6 sometimes helped on a structured page, and PSM 11 often added noise. The sample does not prove quality for untested pages or provide a total usable-page count.

Across all 2,559 pypdf-extracted pages, zero contain Assamese-block Unicode characters. PDFium returned the same garbled strings on sampled font-mapped pages. Several such pages have subsetted Geetanjali fonts and `/ToUnicode` maps, but extracted text does not match the visible Assamese; a map's presence does not establish its correctness. Installing fontTools suppressed one CFF/Type1 parsing warning but did not change the sampled extracted text. The OCR/visual-review flags remain heuristics, not confirmed per-page diagnoses. The fixed 15-page evaluation and the later 50-page pilot do not establish full-corpus quality. The approved resumable full OCR run is separate; its completion report must be inspected before corpus review.

## Phase 2 extraction

The script and report were created/run without changing original books:

```powershell
Set-Location "$HOME\Downloads\assamese_chatbot_ai"
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m scripts.extract_textbooks
```

The script writes page-marked raw extraction and per-page JSON metadata under `data\extracted_text\`, plus timestamped JSON and Markdown reports under `reports\`. It also creates the requested `data\cleaned_text\`, `data\training_data\`, and `checkpoints\` directories; these remain empty in Phases 1–2. No spell correction, cleanup, examples, embeddings, retrieval system, or training was performed.

The first extraction report undercounted likely OCR/font-encoding problems because repeated copyright footer text was counted as usable page text. It also treated those repeated footers as duplicate page content. The corrected report removes matching footer lines only from quality metrics and duplicate fingerprints; the raw extracted text remains unchanged.

The corrected Phase 2 report (`textbook-extraction-20261031-162750.md` and `.json`) records 17 PDFs and 2,559 pages; 1,440,738 raw extracted characters; 1,326,555 characters after excluding matching copyright lines for this metric only; 193,935 whitespace-delimited tokens (an estimate); 2,557 OCR/visual-review candidates; 860 encoding-suspect pages; 135 pages with no substantive extraction and no detected images; zero pypdf page-extraction exceptions; parser warnings in two books; and two duplicate-content groups after footer exclusion. The OCR/encoding flags are deliberately conservative heuristics, not a finding that every flagged page requires OCR. Assamese/Bengali shared script is not treated as a language classifier.

The extraction is **not training-ready**: multiple PDFs return only copyright footers or suspicious font-mapped characters, despite having no page extraction exception. The 193,935 whitespace count includes text that may be garbled and is not a count of usable Assamese or Granite tokens. OCR has not been run. Copyright notice lines are retained in raw extracted output, but matching standalone SCERT notice lines are excluded from substantive-text metrics and duplicate fingerprints. Several PDFs contain a SCERT notice stating that they are not to be republished; do not train on or redistribute them without reviewing rights and obtaining any required permission. The source directory includes a Bengali-medium book and an Arabic (L4) course book; they should not be presumed suitable Assamese training data.

## Sources

- [Kakugo Assamese model card and training recipe](https://huggingface.co/ptrdvn/kakugo-3B-asm)
- [Kakugo model repository file metadata](https://huggingface.co/api/models/ptrdvn/kakugo-3B-asm/tree/main?recursive=true&expand=true)
- [Kakugo config.json](https://huggingface.co/ptrdvn/kakugo-3B-asm/raw/main/config.json)
- [IBM Granite 4.0 Micro model card](https://huggingface.co/ibm-granite/granite-4.0-micro)
- [IBM Granite 4.0 Micro config.json](https://huggingface.co/ibm-granite/granite-4.0-micro/resolve/main/config.json)
- [GraniteMoeHybrid Transformers documentation](https://huggingface.co/docs/transformers/main/en/model_doc/granitemoehybrid)
- [Kakugo authors' training repository](https://github.com/Peter-Devine/kakugo)
- [Hugging Face PEFT LoRA documentation](https://huggingface.co/docs/peft/main/en/developer_guides/lora)
- [Official Tesseract Assamese traineddata metadata](https://api.github.com/repos/tesseract-ocr/tessdata/contents/asm.traineddata)
