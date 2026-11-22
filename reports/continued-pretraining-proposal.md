# Continued pretraining: preparation proposal

Status: **not ready to train**. This report does not download the upstream checkpoint or tokenizer, run training, or upload textbook files. The Ollama model remains the untouched baseline.

## Reverified upstream model metadata

On 2026-10-31, the Hugging Face model API and files were checked without downloading model weights:

- Repository: [`ptrdvn/kakugo-3B-asm`](https://huggingface.co/ptrdvn/kakugo-3B-asm), revision `a6a854a0a680c4c57ec026df014f8f5964da8721`.
- Config architecture: `GraniteMoeHybridForCausalLM`, model type `granitemoehybrid`, 3,402,836,480 parameters, hidden size 2,560, 40 layers, 40 attention heads / 8 KV heads, vocabulary 100,352, context limit 131,072, and BF16 checkpoint dtype.
- Two safetensors shards are listed at 4,918,145,376 and 1,887,565,800 bytes (6,805,711,176 bytes total; about 6.34 GiB). Their weights were not downloaded.
- `tokenizer.json` is 7,153,421 bytes, `vocab.json` 1,612,704 bytes, `merges.txt` 916,646 bytes, plus a tokenizer config and a distinct chat template. These were not downloaded in this audit.
- The model card declares Apache-2.0 and identifies IBM Granite 4.0 Micro as its base. This does not grant rights to the textbook corpus; rights need separate review.
- The model card's published run is **one epoch of full SFT**, not continued pretraining: LlamaFactory, sequence length 8,000, per-device batch 1, BF16, learning rate `1e-5`, cosine schedule, 5% warmup, ZeRO-3. It reports eight RTX 3090 GPUs. This is a useful upstream reference, not a proof of the minimum hardware for this proposed continued-pretraining workload.

The installed Ollama baseline reports Granite, 3.4B, 2,560 embedding size, 131,072 context, and Q4_K_M. `ollama show --modelfile` identifies local GGUF blob `sha256-4187bda703dd0d1b7bdbc247171856478272a0cd05eca9cae5f1047b7de4f26e` and a `{{ .Prompt }}` template. These facts establish broad architecture agreement only. **They do not prove that the local GGUF weights are a quantization of the exact Hugging Face revision above.** No conversion provenance or tensor-by-tensor comparison is available, so exact checkpoint identity remains unverified. Train from the named, licensed upstream BF16 checkpoint if later approved; never attempt to fine-tune the Ollama GGUF.

Transformers 4.57.1 is named in the upstream config, and the published model card demonstrates a Transformers/LlamaFactory-compatible training recipe. The model contains a Granite/Mamba hybrid architecture. LoRA/QLoRA module targets, PEFT compatibility, optimizer support, export, and Ollama conversion have **not** been tested against this revision. The proposal therefore selects full-parameter causal LM training as its target method and does not claim that LoRA or QLoRA is ready.

## Actual local hardware and feasibility

This Windows host was rechecked:

- Intel Core i5-12450H: 8 cores / 12 logical processors.
- Installed RAM: 8,241,954,816 bytes (7.68 GiB), not 16 GiB.
- NVIDIA GeForce GTX 1650: 4,096 MiB VRAM, compute capability 7.5; also Intel UHD Graphics.
- The project's Python environment does not have PyTorch installed. No CUDA/PyTorch training stack was tested.
- Free space on C: was about 111 GiB at the time checked.

The BF16 weights alone require about 6.34 GiB before framework buffers, activations, gradients, or Windows memory. Thus CPU loading/training is not practical on this 7.68 GiB host, and the 4 GiB GTX 1650 cannot hold the full BF16 weights plus training state. Its Turing generation also does not provide BF16 arithmetic. Ollama Q4 inference fitting is not evidence that backpropagation fits.

For 3.40B parameters, full-parameter BF16 training has a raw-state lower bound on the order of **38 GiB** for BF16 weights + BF16 gradients + two FP32 Adam moments, or roughly **51 GiB** if the optimizer keeps an additional FP32 master copy. This excludes activations, CUDA workspaces, fragmentation, and checkpoint buffers. Plan on **at least 64 GiB of GPU memory for a single-GPU full-training experiment**, or distributed sharding. The only concrete successful upstream reference is **8 × 24 GiB RTX 3090 GPUs with ZeRO-3**; use that as the conservative reproducibility target, not as a verified minimum. For LoRA, a 24 GiB BF16 GPU is a plausible test starting point, but support for the hybrid model and actual module targets remain unverified. A 4-bit/QLoRA path is not proposed until framework/kernel support is demonstrated on a disposable GPU test.

The current host is therefore **not a training target**. No repeated memory experiments or training attempts should be made on it. No cloud service has been selected, paid, or used. Do not upload textbook PDFs to a remote machine; a future GPU plan must be local/authorized and use only a rights-cleared, reviewed corpus.

## Proposed first-run configuration

The non-executable proposal is in [`configs/continued_pretraining.proposed.yaml`](../configs/continued_pretraining.proposed.yaml). It records:

- causal next-token objective on human-approved Assamese text only;
- sequence length 2,048, per-device microbatch 1, gradient accumulation 8, gradient checkpointing, BF16, AdamW, `1e-5` learning rate, cosine scheduler, 3% warmup, and one initial epoch;
- training/validation split by **source book**, not pages, to prevent within-book page leakage;
- loss/perplexity evaluation and checkpoint + optimizer-state saving every 100 steps, retaining three checkpoints for resume.

These are initial engineering choices, not validated hyperparameters. In particular, sequence length and schedule need a short GPU smoke test and validation-loss monitoring before any full run. Training remains blocked until the dataset and compatibility gates in the YAML are completed. Do not treat this proposal as a command to install PyTorch/Transformers or fetch the 6.34 GiB checkpoint.

## OCR and corpus status

Full OCR was requested with the existing resumable runner: Tesseract `asm`, OEM 1, PSM 3, pypdfium2 300 DPI. Completed pilot pages are reused by source PDF SHA-256 and settings ID; failures are persisted and retried. OCR output remains raw under `data/ocr_text/`, separate from `data/cleaned_text/`.

The current OCR runner's confidence and language flags are triage signals only. English/Bengali classifier predictions and low confidence require visual review; high confidence is not an approval. The review-manifest and corpus builder in [`scripts/prepare_training_corpus.py`](../scripts/prepare_training_corpus.py) creates an all-pending page review manifest and will include only pages explicitly approved by a named human reviewer with a timestamp. It preserves page/book boundaries and does no automatic translation, rewriting, de-duplication, or header/footer removal. It creates book-disjoint splits only after there are approved pages from at least two books. Exact model-tokenizer counts remain unavailable until the verified tokenizer files are supplied locally; whitespace-token and Unicode distribution metrics are explicitly labeled estimates.

Create a review manifest after OCR completes:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_training_corpus --create-review-manifest --manifest data\training_data\ocr-review-manifest.json
```

Render any requested OCR page alongside its original PDF image, text, confidence, classifier output, and verified source PDF hash:

```powershell
.\.venv\Scripts\python.exe -m scripts.render_ocr_review_page --book "Ami Aru Amar Paribesh_Class V_Assamese.pdf" --page 36
```

Only after pages have been checked against their original PDF images and the manifest has been updated with reviewer/status/timestamp fields, build the separate corpus:

```powershell
.\.venv\Scripts\python.exe -m scripts.prepare_training_corpus --build --manifest data\training_data\ocr-review-manifest.json
```

This builder refuses to create a corpus with no human-approved pages, refuses OCR text changed after review, and requires a book-disjoint train and validation split. No SFT examples are generated in this phase.

## Remaining gates before training

1. Finish full OCR and inspect its completed per-book and overall reports.
2. Human-review source PDF pages and approve/exclude them in the manifest; resolve book rights before training.
3. Build and audit the book-disjoint corpus; obtain exact tokenizer counts after separately approving/acquiring the small tokenizer files.
4. Preserve and identify the original Ollama GGUF baseline, acquire the upstream checkpoint only with approval, and verify tokenizer/config/model loading at the pinned revision.
5. On compatible GPU hardware, prove a forward/backward causal-LM loss step, optimizer step, adapter/weight change, save/resume, and evaluation before scaling up.
6. Only then finalize the configuration and run continued pretraining. Evaluate against the unchanged Ollama baseline on a fixed Assamese set. SFT remains a separate later approval.
