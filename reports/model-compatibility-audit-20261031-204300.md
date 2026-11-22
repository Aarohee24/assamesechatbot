# Kakugo Checkpoint Compatibility Audit

Audit date: 2026-10-31  
Project: `C:\Users\aaroh\Downloads\assamese_chatbot_ai`  
Scope: verify the available trainable model, tokenizer, runtime relationship, licenses, and local hardware before training.

## Result

**Training is not ready to start.** The upstream Kakugo safetensors checkpoint and tokenizer are available in Hugging Face repository metadata, but neither was downloaded or loaded. The exact relationship between that checkpoint and the installed Ollama GGUF is not verifiable from the local Ollama metadata. The current computer is not capable of practical 3.4B training. No model files were downloaded, no data was uploaded, and no training was attempted.

## Upstream Kakugo repository

The upstream model linked from the Kakugo model card is [`ptrdvn/kakugo-3B-asm`](https://huggingface.co/ptrdvn/kakugo-3B-asm), pinned for this audit at revision `a6a854a0a680c4c57ec026df014f8f5964da8721`. Its model card links to the Kakugo project code and describes the model as a fine-tune of IBM Granite 4.0 Micro.

Hugging Face's model API and the pinned `config.json` report:

| Property | Verified metadata |
|---|---|
| Transformers architecture | `GraniteMoeHybridForCausalLM` |
| Model type | `granitemoehybrid` |
| Parameters | 3,402,836,480 |
| Checkpoint dtype | BF16 |
| Hidden size | 2,560 |
| Layers | 40 |
| Attention heads / KV heads | 40 / 8 |
| Configured layer types | 40 entries, all `attention` |
| Vocabulary | 100,352 |
| Maximum positions | 131,072 |
| Config's Transformers version | 4.57.1 |
| License declared by model card | Apache-2.0 |

Two trainable safetensors shards are listed: 4,918,145,376 and 1,887,565,800 bytes (6,805,711,176 bytes total, about 6.34 GiB). This verifies that a Hugging Face-format checkpoint is published; it does not verify its successful loading in this environment.

The same repository lists `tokenizer.json` (7,153,421 bytes), `vocab.json` (1,612,704 bytes), `merges.txt` (916,646 bytes), `tokenizer_config.json`, `special_tokens_map.json`, and a separate `chat_template.jinja`. These files are available upstream but are **not present in the project's `checkpoints` directory**. The Ollama model does not expose a tokenizer file or prove that its tokenizer and chat template are identical to this revision.

Apache-2.0 permits modification and redistribution subject to its terms and notices. This does not grant rights to the textbooks: publisher/license and training-use permission must be checked separately before any training or sharing of data or derived weights.

## Local Ollama model identity

The installed model is `trubits/kakugo-3b-asm:q4_k_m`. `ollama show` reports Granite, 3.4B parameters, 2,560 embedding width, 131,072 context, and Q4_K_M. `ollama show --modelfile` points to local GGUF blob `sha256-4187bda703dd0d1b7bdbc247171856478272a0cd05eca9cae5f1047b7de4f26e`, whose local size is 2,099,503,232 bytes. The GGUF uses the template `{{ .Prompt }}`.

These facts agree at a broad architecture/size level with the upstream checkpoint. They do **not** prove the GGUF was quantized from `ptrdvn/kakugo-3B-asm` at this revision: the publisher namespace differs, and the GGUF metadata supplies no source-revision or tensor-hash provenance. Do not convert the trained checkpoint by assuming that it is the exact parent of this GGUF. Preserve the installed Ollama model as the baseline.

## Training-library and adapter compatibility

- The project `.venv` currently has **none** of `torch`, `transformers`, `peft`, `bitsandbytes`, `accelerate`, or `deepspeed` installed.
- The separate system Python has Transformers 5.9.0 and can import the `GraniteMoeHybridForCausalLM` class. This is not the project's virtual environment and is not a test of loading the checkpoint or running training.
- The model config declares Transformers 4.57.1. The model card's published recipe uses `trust_remote_code: true`, LlamaFactory, full-parameter SFT, BF16, and DeepSpeed ZeRO-3. It does not publish a LoRA/QLoRA recipe.
- LoRA target layers, PEFT support, quantized training kernels, checkpoint export, and Ollama conversion were not tested. PEFT is absent from the project environment. Despite the `GraniteMoeHybridForCausalLM` class name and Mamba-related config fields, this pinned config lists all 40 layers as `attention`; inspect the actual checkpoint/module names before selecting adapter targets. **LoRA and QLoRA compatibility remain unverified.**
- Continued pretraining with causal next-token loss is conceptually compatible with a causal LM, but the Kakugo card only documents supervised fine-tuning. It is not evidence that a textbook continued-pretraining recipe or hyperparameters have been validated.

## Actual local hardware

Measured on this Windows machine:

- Intel Core i5-12450H: 8 cores / 12 logical processors.
- Installed RAM: 8,241,954,816 bytes (about 7.68 GiB).
- NVIDIA GeForce GTX 1650: 4 GiB VRAM; NVIDIA reports no active GPU process at the time checked. The GPU is compute capability 7.5 and does not support BF16 arithmetic.
- Free space on C: about 110.4 GiB.

The BF16 model weights alone need about 6.34 GiB, before Windows, framework memory, gradients, activations, and work buffers. They cannot fit in the 4-GiB GPU, and host memory is already too small for a practical CPU load/training run. **Do not attempt CPU training on this computer.** A quantized Ollama inference model fitting on the machine does not imply that backpropagation fits.

For 3.40B parameters, a rough full-parameter BF16 training-state floor is about 38 GiB (BF16 weights and gradients plus FP32 Adam moments), or about 51 GiB if FP32 master weights are also held, before activations and CUDA workspaces. Use **at least 64 GiB GPU VRAM as the conservative single-GPU starting requirement** for full-parameter training, subject to a real memory smoke test. The model card's concrete full-training reference is 8 × 24-GiB RTX 3090 GPUs with ZeRO-3; that is a reproducibility reference, not a proven minimum for continued pretraining. There is no verified minimum VRAM for LoRA on this hybrid model; 24 GiB would only be a possible disposable compatibility-test starting point, not a guarantee.

## Decision and remaining gates

1. Do not train from the Ollama GGUF.
2. Do not download the 6.34-GiB upstream checkpoint or tokenizer until a suitable training host and compatible, pinned software stack are selected.
3. Before any run, load the pinned safetensors and tokenizer together in the intended environment, verify a forward/backward optimizer step changes weights, and establish exact PEFT/LoRA targets if adapter training is selected.
4. Do not call the trained result a replacement for the installed Ollama model until export and inference compatibility are demonstrated; their exact weight lineage is not established.
5. Keep training blocked until approved textbook pages produce a reviewed corpus and textbook training rights are resolved. No unreviewed OCR is training-ready.

Sources checked without downloading weights: [Kakugo model card and repository](https://huggingface.co/ptrdvn/kakugo-3B-asm), [pinned model config](https://huggingface.co/ptrdvn/kakugo-3B-asm/blob/a6a854a0a680c4c57ec026df014f8f5964da8721/config.json), and [Ollama model listing](https://ollama.com/trubits/kakugo-3b-asm:q4_k_m).
