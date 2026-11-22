import time

from config import AppConfig
from ollama_client import OllamaClient, OllamaError


PROMPTS = (
    "নমস্কাৰ! আপুনি কোন? নিজৰ বিষয়ে অসমীয়াত কওক।",
    "অসমীয়া AI সহায়ক হিচাপে নিজৰ পৰিচয় দিয়ক।",
    "অসমীয়া ভাষাৰ বিষয়ে পাঁচটা সম্পূৰ্ণ বাক্য লিখক।",
)


def main() -> None:
    config = AppConfig(request_timeout=300, num_predict=1024)
    client = OllamaClient(config)
    print(f"MODEL={config.model_name} NUM_PREDICT={config.num_predict} STREAM=False")

    if not client.model_available():
        raise SystemExit(f"Required model is not installed: {config.model_name}")

    failed_prompts = []
    for index, prompt in enumerate(PROMPTS, start=1):
        started = time.perf_counter()
        print(f"\n--- TEST {index}: {prompt} ---")
        try:
            response = client.chat([], prompt, num_predict=1024, history_messages=12)
        except OllamaError as error:
            print(f"ERROR={type(error).__name__}: {error}")
            failed_prompts.append(index)
            continue

        print(f"RESPONSE={response.content}")
        print(
            f"DONE={response.done!r} DONE_REASON={response.done_reason!r} "
            f"COMPLETE={response.is_complete} "
            f"LATENCY_SECONDS={time.perf_counter() - started:.2f}"
        )

    if failed_prompts:
        raise SystemExit(f"Live model request failed for test(s): {failed_prompts}")


if __name__ == "__main__":
    main()
