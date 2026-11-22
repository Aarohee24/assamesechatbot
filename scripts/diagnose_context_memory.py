from pathlib import Path
import sys

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config import AppConfig


MESSAGES = [
    {
        "role": "system",
        "content": "আপুনি এজন অসমীয়া AI সহায়ক। কেৱল স্বাভাৱিক অসমীয়াত উত্তৰ দিয়ক।",
    },
    {
        "role": "user",
        "content": "মোৰ নাম ৰাহুল। মই অষ্টম শ্ৰেণীত পঢ়োঁ আৰু বিজ্ঞান ভাল পাওঁ।",
    },
    {
        "role": "assistant",
        "content": "আপোনাক লগ পাই ভাল লাগিল, ৰাহুল।",
    },
    {
        "role": "user",
        "content": "মোৰ নাম কি? মই কোন শ্ৰেণীত পঢ়োঁ আৰু কোনটো বিষয় ভাল পাওঁ?",
    },
]


def main() -> int:
    config = AppConfig.from_env()
    session = requests.Session()
    session.trust_env = False

    try:
        response = session.post(
            f"{config.base_url}/api/chat",
            json={
                "model": config.model_name,
                "messages": MESSAGES,
                "stream": False,
                "think": False,
                "options": {
                    "temperature": config.temperature,
                    "num_predict": config.num_predict,
                },
            },
            timeout=(5, config.request_timeout),
            allow_redirects=False,
        )
    except requests.Timeout:
        print("Ollama timed out before completing the diagnostic.", file=sys.stderr)
        return 1
    except requests.ConnectionError:
        print("Could not connect to the local Ollama service.", file=sys.stderr)
        return 1

    if 300 <= response.status_code < 400:
        print("Ollama returned an unexpected redirect.", file=sys.stderr)
        return 1
    try:
        response.raise_for_status()
    except requests.HTTPError as error:
        print(f"Ollama returned HTTP {response.status_code}: {error}", file=sys.stderr)
        return 1

    try:
        data = response.json()
    except ValueError:
        print("Ollama returned malformed JSON.", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("Ollama returned an unexpected response format.", file=sys.stderr)
        return 1
    if isinstance(data.get("error"), str):
        print(f"Ollama error: {data['error']}", file=sys.stderr)
        return 1

    message = data.get("message")
    answer = message.get("content") if isinstance(message, dict) else None
    if not isinstance(answer, str) or not answer.strip():
        print("Ollama returned an empty or invalid assistant response.", file=sys.stderr)
        return 1

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print("Assistant response:")
    print(answer.strip())
    print(f"\ndone: {data.get('done')!r}")
    print(f"done_reason: {data.get('done_reason')!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
