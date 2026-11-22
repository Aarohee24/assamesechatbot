# Kakugo Model and Training Readiness Audit

Audit date: 2026-11-01  
No model weights were downloaded; no training was started; no book data was uploaded.

## Upstream model and tokenizer

The pinned upstream repository is [`ptrdvn/kakugo-3B-asm`](https://huggingface.co/ptrdvn/kakugo-3B-asm), revision `a6a854a0a680c4c57ec026df014f8f5964da8721`. Its model card and repository metadata declare Apache-2.0 and publish two BF16 safetensors shards totaling 6,805,711,176 bytes (about 6.34 GiB).

The pinned configuration identifies:

- Architecture: `GraniteMoeHybridForCausalLM` (`granitemoehybrid`).
- Parameters: 3,402,836,480.
- Hidden width 2,560; 40 layers; 40 attention heads / 8 KV heads.
- Vocabulary size 100,352; maximum sequence positions 131,072.
- BF16 checkpoint dtype; config generated for Transformers 4.57.1.
- The architecture class is present in the installed system Transformers 5.9.0.

Only the small tokenizer assets were downloaded from the pinned upstream revision into `checkpoints/kakugo-tokenizer` (about 10 MiB total). No safetensors weight files were downloaded. With the installed system Transformers 5.9.0, `AutoTokenizer` loaded this directory locally as `GPT2Tokenizer`; it reports 100,352 tokens, matching the upstream model config. A sample Assamese/Latin technical-term string encoded and decoded losslessly. This establishes tokenizer/config vocabulary agreement and basic decoding, not a loaded-model forward pass.

The tokenizer is from the exact Kakugo repository/revision, rather than a newly trained vocabulary. The Ollama GGUF tokenizer has not been extracted or compared token-by-token.

## Ollama GGUF relationship

The installed `trubits/kakugo-3b-asm:q4_k_m` GGUF is 2,099,503,232 bytes and reports Granite, 3.4B parameters, 2,560 embedding width, 131,072 context, and Q4_K_M. This is broad architecture agreement only. The GGUF blob metadata provides no upstream repository revision or matching tensor hashes, so **its exact identity as a quantization of the pinned Kakugo safetensors checkpoint is unverified**. GGUF quantized weights are not the training input. Keep the existing Ollama model unchanged as the inference baseline.

## Fine-tuning support

- The Kakugo card documents a full-parameter SFT using LlamaFactory/Transformers, BF16, and DeepSpeed ZeRO-3. It reports 8 × 24-GiB RTX 3090 GPUs; this is a published reference, not a proven minimum for this continued-pretraining task.
- Causal next-token training is the architecture's native objective and a full-parameter Transformers continued-pretraining script is prepared. Actual checkpoint loading, backward pass, and weight update have **not** been tested because weights were intentionally not downloaded.
- PEFT LoRA target layers and save/merge/export behavior are unverified. QLoRA is also unverified. The project environment has no PyTorch, Transformers, or PEFT, so this pipeline does not claim adapter support or use LoRA/QLoRA.
- Textbook redistribution/training rights are independent of Apache-2.0 model rights and have not been verified.

## Hardware recheck

Measured locally on 2026-11-01:

- Intel Core i5-12450H: 8 cores / 12 logical processors.
- System RAM: 8,241,954,816 bytes (7.68 GiB).
- NVIDIA GeForce GTX 1650: 4 GiB VRAM, currently unused; BF16 is unsupported on its compute capability 7.5.
- C: free space was about 112.8 GiB.
- Project `.venv` lacks PyTorch, Transformers, PEFT, Accelerate, DeepSpeed, and bitsandbytes.

The local PC is **not suitable for 3.4B full-parameter training**. The project training script checks for CUDA, BF16, one GPU with at least 64 GiB VRAM, local model and tokenizer files, and book-disjoint train/validation records before loading any base weights. Recommended target is a single 80-GiB A100/H100-class GPU; a 64-GiB device is only a minimum smoke-test starting point. The script does not implement distributed ZeRO or adapters.

## Decision

The pinned upstream checkpoint format, architecture metadata, license declaration, and tokenizer vocabulary are verified from public metadata; the small tokenizer has been loaded locally. A model load/backpropagation smoke test and PEFT support remain unverified. The local GPU cannot train it. Use a compatible GPU host and download the pinned safetensors there only after deciding the textbook rights and accepting that automatic OCR may be wrong. No cloud environment was chosen or used.
