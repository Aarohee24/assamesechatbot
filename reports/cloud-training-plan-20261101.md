# GPU Continued-Pretraining Execution Plan

Status: prepared only. This document contains no cloud selection, payment, upload, model-weight download, or training run.

## Recommended hardware and storage

- Recommended: one NVIDIA A100 80-GiB or H100 80-GiB GPU, CUDA, and at least 16 CPU cores / 64 GiB host RAM.
- Minimum gate in the prepared full-parameter script: one BF16-capable CUDA GPU with 64 GiB VRAM. This is a conservative minimum to test, not a guarantee of fit; abort if the model load or first optimizer step exceeds memory.
- Do not use the local GTX 1650 4-GiB GPU or CPU.
- Keep at least **150 GiB free scratch disk**. The BF16 base checkpoint is about 6.34 GiB. Full Adam optimizer state and periodic resumable checkpoints can each occupy tens of GiB; the script retains up to three checkpoints. Current filtered datasets are much smaller than the weights but still need to be copied to the host.
- LoRA might reduce memory, but module targets and PEFT/QLoRA support for this revision have not been verified. This prepared script uses full-parameter training only.

## Installation and pinned checkpoint acquisition

Run these commands only on a compatible GPU host. Python 3.11 is recommended. Install a PyTorch CUDA build that matches the host driver using the official PyTorch selector; for a CUDA 12.8 wheel where available:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install torch --index-url https://download.pytorch.org/whl/cu128
python -m pip install -r requirements-training.txt
python -m pip install "huggingface_hub[cli]"
```

Only after verifying the host and confirming data rights, download the **pinned original trainable checkpoint**, not the Ollama GGUF:

```bash
hf download ptrdvn/kakugo-3B-asm \
  --revision a6a854a0a680c4c57ec026df014f8f5964da8721 \
  --local-dir checkpoints/kakugo-3b-asm
```

The project already contains the small pinned tokenizer in `checkpoints/kakugo-tokenizer`. Verify its vocabulary is 100,352 and that the downloaded model configuration uses `GraniteMoeHybridForCausalLM` before training.

## Optional dataset transfer (not executed)

No book data has been uploaded. OCR-derived text may be publisher-restricted. Only transfer it after the owner has explicitly approved the destination and verified the applicable rights. The following is an example placeholder, not a command run by this project:

```bash
scp -r data/training_data/auto_filtered_assamese.jsonl \
  data/training_data/processed user@YOUR_APPROVED_GPU_HOST:/workspace/assamese_chatbot_ai/data/training_data/
```

Also transfer this repository's `scripts/train_continued_pretraining.py`, `requirements-training.txt`, and the reviewed execution config. Keep the original PDFs and raw OCR off the GPU host unless separately needed and explicitly authorized; the training script only reads the processed JSONL datasets.

## Preflight and training

From the project directory on that GPU host, first run a no-weight-load preflight:

```bash
python scripts/train_continued_pretraining.py \
  --allow-automatic-ocr \
  --model-dir checkpoints/kakugo-3b-asm \
  --tokenizer-dir checkpoints/kakugo-tokenizer
```

It verifies hardware, source-book separation, tokenizer/model vocabulary, architecture, and local files. It does not load base weights unless execution is explicitly requested. Start the actual full-parameter continued-pretraining run only after preflight passes:

```bash
python scripts/train_continued_pretraining.py \
  --execute \
  --allow-automatic-ocr \
  --model-dir checkpoints/kakugo-3b-asm \
  --tokenizer-dir checkpoints/kakugo-tokenizer \
  --train-jsonl data/training_data/processed/train.jsonl \
  --validation-jsonl data/training_data/processed/validation.jsonl \
  --output-dir checkpoints/continued-pretraining-run-01
```

The explicit acknowledgment flag is required because the source OCR is automatically filtered, not human-verified. Training is causal next-token prediction with full-model weight updates, sequence length 2,048, per-device batch 1, gradient accumulation 8, BF16, gradient checkpointing, AdamW, cosine schedule, and one epoch. Checkpoints contain optimizer state to resume; validation loss/perplexity and sampled weight-change verification are recorded. Resume an interrupted run by adding `--resume` with the same output directory. Never point this script at the quantized Ollama blob.
