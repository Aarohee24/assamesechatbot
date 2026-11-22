# অসমীয়া AI সহায়ক

A locally run Assamese chat interface built with Streamlit and llama.cpp. It serves the fine-tuned model from `models\assamese-corrected-q4_k_m.gguf`; it does not use Ollama, RAG, cloud inference, paid APIs, or API keys. Chats remain in Streamlit's browser session.

## Architecture

Streamlit validates each non-empty prompt with a local Assamese/Bengali language classifier, then sends it to the local llama.cpp OpenAI-compatible chat endpoint (`http://127.0.0.1:8081/v1/chat/completions`). The launcher starts the bundled CPU-only llama.cpp server with the GGUF's embedded Jinja chat template, context size 1024, batch size 32, micro-batch size 16, one parallel slot, and no GPU offload. A persistent Assamese system instruction precedes recent complete turns. The client checks the completion finish reason; empty, malformed, or length-limited responses are not shown or saved. The app removes a well-formed `<think>...</think>` block before output validation, rejects malformed internal tags, and uses the local classifier to reject uncertain output. Only a complete response that passes output validation is displayed and added to session history. No fallback to Ollama or another model is configured.

## Assamese-only language identification

The app uses [AI4Bharat IndicLID-FTN](https://huggingface.co/ai4bharat/IndicLID-FTN), a local FastText classifier with distinct native-script labels for Assamese (`asm_Beng`) and Bengali (`ben_Beng`) and labels for English and Hindi. Assamese is accepted only when the classifier predicts Assamese with confidence at least `0.75`. Empty, punctuation-only, number-only, and inputs with fewer than four Unicode letters are rejected without invoking the classifier; other low-confidence or non-Assamese inputs receive `অনুগ্ৰহ কৰি কেৱল অসমীয়া ভাষাত প্ৰশ্ন লিখক।`. Romanized Assamese is not an IndicLID-FTN native-script class and is conservatively rejected. No Unicode script range is used as the language decision.

NE-LID was investigated but not selected: its published 11-language label list does not include Bengali, so it cannot explicitly distinguish Bengali from Assamese. PyPI `ne-lid` 1.0.1 documents `from ne_lid import NELID; NELID().predict(text)`, depends on `fasttext-wheel`, `huggingface-hub`, and `numpy<2`, and downloads weights on the first `NELID()` construction to the Hugging Face cache. Its current Hugging Face model file is about 838 MB despite the model card's smaller size claim. Its published labels do not include Bengali. IndicLID-FTN was chosen because its documented classes separate Assamese and Bengali and its classifier is smaller.

Install the pinned FastText Windows wheel and Hugging Face Hub dependency along with the app:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

The classifier weights are **not included in this project**. On the first app run, `huggingface_hub.hf_hub_download` downloads the pinned 260.5 MB `model_baseline_roman.bin` from the IndicLID-FTN repository; inference thereafter is local. The default Hugging Face cache on Windows is under `%USERPROFILE%\.cache\huggingface\hub` (about 260.5 MB, plus cache overhead). Set `HF_HOME` before starting Streamlit to choose another cache directory. A first-use network connection to Hugging Face is needed only to retrieve this classifier artifact; user prompts and inference are not sent there. Hugging Face caching may use symlinks; on Windows without Developer Mode or administrator rights it falls back to copying and can require additional disk space. `numpy<2` is required because the installed FastText wheel uses a NumPy 1.x API.

The IndicLID-FTN model repository identifies its license as **MIT**. See the [model repository](https://huggingface.co/ai4bharat/IndicLID-FTN) for the license metadata and preserve the applicable license/copyright notice when redistributing the model. The [FastText wheel](https://pypi.org/project/fasttext-wheel/) is also MIT-licensed; [Hugging Face Hub](https://pypi.org/project/huggingface-hub/) is Apache-2.0. IndicLID's published evaluation is not a guarantee of accuracy on every Assamese/Bengali sentence, code-mixed text, proper name, or short prompt. Uncertain predictions are rejected; false accepts and false rejects remain possible.

## Hardware and prerequisites

- Windows 10/11, Python 3.10 or newer, and the corrected model file at `models\assamese-corrected-q4_k_m.gguf` (about 2.1 GB). The existing `models\assamese-q4_k_m.gguf` is an incompatible conversion and is not used.
- The bundled llama.cpp b12032 CPU runtime is used; Ollama is not required. Its `--list-devices` reports `(none)` and its installed backends are CPU-only, so the GTX 1650 cannot currently be used by this build. The launcher explicitly sets `-ngl 0`; GPU offload is not enabled or claimed to improve performance.
- The 8 GB RAM configuration is constrained. The launcher refuses to start unless at least 3 GiB of physical RAM is available. Close other memory-heavy applications yourself before launch and keep several GB of free disk space for Windows paging and logs. This floor is not a guarantee of stable inference. CPU generation may be slow; the model's advertised maximum context is not practical here.
- The server uses one request slot and modest prompt/evaluation batches to limit temporary memory. llama.cpp's default memory mapping is retained (the launcher does not use `--no-mmap`), avoiding an unnecessary second explicit model copy. When you exit the launcher, its `finally` cleanup stops the Streamlit and model-server processes it started; an already-running matching server is reused and is not stopped by this launcher.
- The current runtime cannot establish whether partial GPU offload would improve speed or fit safely. That requires a separate CUDA-enabled llama.cpp build and a measured trial with VRAM monitoring; this project does not install or switch runtimes automatically.
- If startup reports `check_tensor_dims: tensor 'blk.0.ssm_in.weight' not found`, the GGUF metadata says the layers are recurrent while the tensor file has attention weights and no SSM tensors. This is a conversion-artifact inconsistency, not a RAM, batch-size, or context setting. The preflight rejects this mismatch before loading. Repair requires regenerating a GGUF from the existing merged checkpoint with a converter that writes the all-attention architecture metadata consistently; the current GGUF is left untouched.

## Rebuild the corrected GGUF

The existing `models\assamese-q4_k_m.gguf` has inconsistent hybrid metadata and is deliberately not overwritten. A vocabulary-only converter probe confirmed that the staged checkpoint produces the correct dense `granite` architecture and a positive KV-head count on all 40 attention layers. To create separate corrected FP16 and Q4_K_M files from the local merged checkpoint:

```powershell
.\scripts\convert_corrected_gguf.ps1
.\scripts\convert_corrected_gguf.ps1 -Execute
```

The first command validates local inputs without loading checkpoint weights. Before executing, close memory-heavy apps yourself and ensure Windows reports at least **3 GiB available RAM** and **20 GiB free disk**. The execution converts the existing staged checkpoint to `models\assamese-corrected-f16.gguf`, validates its architecture and all attention tensors, quantizes it with the bundled llama.cpp quantizer to `models\assamese-corrected-q4_k_m.gguf`, then validates the Q4_K_M result. It refuses to overwrite either new output and verifies the source checkpoint and old GGUF hashes remain unchanged. No model is downloaded or retrained.

The chatbot launcher uses only `assamese-corrected-q4_k_m.gguf`; if conversion has not completed and passed validation, startup stops rather than falling back to the old file.
- The local IndicLID classifier is downloaded on first use as described above; no model weights are downloaded by the chatbot launcher.

## Windows setup

Double-click `run_chatbot.bat`, or open PowerShell in the project directory and run:

```powershell
.\scripts\start_chatbot.ps1
```

`run_chatbot.bat` creates `.venv` if needed and installs the listed dependencies only when required. It does not upgrade global Python packages, download model weights, or register an Ollama model. The PowerShell launcher verifies the GGUF metadata, starts the bundled llama.cpp server if the expected local model is not already running, waits for Streamlit, and opens the browser. Startup logs are written to `logs\`.

The app is available at **http://127.0.0.1:8501**. Leave the launcher window open while chatting. Press **Ctrl+C** in that window to stop the app and the llama.cpp process started by that launcher. It does not stop a server that was already running.

The app provides a message input, submit control, conversation history, clear-chat option, loading indicator, and visible error messages. New Chat and Clear Conversation clear only the current browser session's history. Assamese input/output validation remains enabled.

## Configuration

Defaults are local and conservative. Set these environment variables before launching to override them:

| Variable | Default | Meaning |
|---|---|---|
| `LLAMA_CPP_BASE_URL` | `http://127.0.0.1:8081` | Local llama.cpp API. Only loopback addresses are accepted. |
| `LLAMA_CPP_MODEL` | `assamese-q4-k-m` | Exact local server model alias. No other model is used as fallback. |
| `LLAMA_CPP_TEMPERATURE` | `0.7` | Generation temperature (0 through 2). |
| `LLAMA_CPP_NUM_PREDICT` | `512` | Maximum response tokens. |
| `CHAT_HISTORY_MESSAGES` | `4` | Maximum prior messages included with the system prompt and current prompt (the UI retains the full session history). |
| `LLAMA_CPP_TIMEOUT_SECONDS` | `300` | Model response read timeout. |

The app validates its configuration and refuses non-local API URLs.

## Tests and live Assamese checks

Run the unit tests without loading the GGUF or starting llama.cpp:

```powershell
Set-Location "$HOME\Downloads\assamese_chatbot_ai"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

After the launcher reports that the exact GGUF alias is loaded, enter Assamese prompts in the app, for example:

1. `নমস্কাৰ! আপুনি কেনে আছে?`
2. `আপুনি কোন আৰু আপুনি কি কাম কৰিব পাৰে?`
3. `অসমৰ বিষয়ে সহজ অসমীয়াত বৰ্ণনা কৰক।`
4. `কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ ভাষাত বুজাই দিয়ক।`
5. `মই এটা বিষয় বুজি পোৱা নাই। আপুনি মোক সহায় কৰিব পাৰিবনে?`
6. `মই আজি ভাল অনুভৱ কৰা নাই। মোৰ লগত কথা পাতিবনে?`
7. `আগৰ উত্তৰটো আৰু সহজকৈ বুজাই দিয়ক।`

### Historical Ollama model check (2026-10-29; not the deployed GGUF)

These results belong to the earlier, separately installed `trubits/kakugo-3b-asm:q4_k_m` Ollama model. They are not tests of `models\assamese-q4_k_m.gguf`, and do not establish that the current llama.cpp deployment has generated a response.

| Prompt | Latency | Observed result |
|---|---:|---|
| `নমস্কাৰ! আপুনি কোন? নিজৰ বিষয়ে অসমীয়াত কওক।` | 4.74 s | Complete Assamese response, but described itself as a helping “machine” instead of giving the requested assistant name. It did not claim to be ChatGPT. |
| `অসমীয়া AI সহায়ক হিচাপে নিজৰ পৰিচয় দিয়ক।` | 9.35 s | Complete response; it began “মই অসমীয়া AI সহায়ক।” |
| `অসমীয়া ভাষাৰ বিষয়ে পাঁচটা সম্পূৰ্ণ বাক্য লিখক।` | 12.70 s | Returned five numbered sentences and stopped normally, but included a visible `<think>` preamble and some awkward or questionable statements. |

At `num_predict=512`, prompts 2 and 3 returned `done_reason='length'`; the earlier Ollama app raised its limit to 1024. Identity adherence was inconsistent and grammatical/factual quality is not assured. These results are a small sample, not an accuracy or fluency evaluation.

To run a current check, launch the chatbot with `run_chatbot.bat` and test prompts in the browser. The historical Ollama check script is not part of the current deployment path.

```powershell
Set-Location "$HOME\Downloads\assamese_chatbot_ai"
.\.venv\Scripts\python.exe -m scripts.live_model_check
```

### Language-classifier smoke check (2026-10-29)

The real pinned IndicLID-FTN model was downloaded to the Hugging Face cache and run locally against the samples in `scripts/check_language_detector.py`. The gate matched all **16/16 expected decisions** in this small hand-picked set:

| Input set | Results |
|---|---|
| 6 Assamese sentences, including numbers, Assamese names, `Python`, `API`, `Streamlit`, and `chatbot` | 6/6 accepted as `asm_Beng`; top confidence 0.9988–1.0. |
| 4 Bengali sentences in the shared Bengali-Assamese script | 4/4 identified as `ben_Beng` and rejected; confidence 0.9969–1.0. |
| 2 English sentences | 2/2 rejected. |
| 2 Hindi sentences | 2/2 rejected. One was labelled Maithili (`mai_Deva`) rather than Hindi; it was still correctly rejected as non-Assamese. |
| Romanized Assamese and mixed English-Assamese | 2/2 rejected (Romanized text was not classified as Assamese; the mixed greeting was caught by the English marker check). |

This is not a representative benchmark and does not establish a general error rate. In particular, IndicLID is a classifier rather than a guarantee; unusual wording, very short text, named entities, and code-mixing may still be misclassified. The acceptance threshold is `0.75`; very short text is rejected before classification, and English marker words are rejected in mixed text while common technical terms, code spans, and URLs are allowed.

Run the deterministic validator and chat-flow tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests mock the classifier and local llama.cpp API; they do not download or load the GGUF. Run the real classifier smoke check with:

```powershell
.\.venv\Scripts\python.exe -m scripts.check_language_detector
```

This loads the cached classifier and prints each label, score, and decision.

The earlier Ollama model was checked through the Assamese input/output gate: `নমস্কাৰ, আপুনি কেনে আছে?` was accepted, and one generated response passed as `asm_Beng` with confidence 1.0. A Bengali prompt (`নমস্কার, আপনি কেমন আছেন?`) was rejected with the required Assamese message and never reached that model. This is historical validation evidence, not a test of the current GGUF runtime.
