from collections.abc import Mapping, Sequence
import re


SYSTEM_PROMPT = (
    "You are অসমীয়া AI সহায়ক, an assistant that communicates only in Assamese. "
    "Every user message reaching you has already passed Assamese-language validation. "
    "Answer only in natural Assamese, using Assamese script. Do not answer in English, "
    "Hindi, Bengali, or any other language. Do not identify yourself as ChatGPT. If asked "
    "your identity, introduce yourself as অসমীয়া AI সহায়ক. Use complete sentences, "
    "answer the user's question directly, and acknowledge uncertainty when needed. "
    "Do not reveal internal reasoning or emit <think> tags."
)

THINK_BLOCK_PATTERN = re.compile(r"<think\b[^>]*>.*?</think\s*>", re.IGNORECASE | re.DOTALL)
THINK_MARKER_PATTERN = re.compile(r"</?think\b", re.IGNORECASE)


def sanitize_assistant_response(response: str) -> str | None:
    sanitized = THINK_BLOCK_PATTERN.sub("", response).strip()
    if THINK_MARKER_PATTERN.search(sanitized):
        return None
    if re.search(r"<\|(?:im|fim|end|start)[^|]*\|>", sanitized, re.IGNORECASE):
        return None
    return sanitized or None


def build_messages(
    history: Sequence[Mapping[str, object]],
    prompt: str,
    max_history_messages: int,
) -> list[dict[str, str]]:
    if not prompt.strip():
        raise ValueError("Message cannot be empty.")
    if max_history_messages < 0:
        raise ValueError("History message limit must not be negative.")

    completed_turns: list[tuple[dict[str, str], dict[str, str]]] = []
    pending_user: dict[str, str] | None = None
    for message in history:
        role = message.get("role")
        content = message.get("content")
        if (
            not isinstance(role, str)
            or role not in {"user", "assistant"}
            or not isinstance(content, str)
            or not content.strip()
        ):
            continue
        normalized = {"role": role, "content": content}
        if role == "user":
            pending_user = normalized
        elif pending_user is not None:
            if message.get("complete", True) is True:
                completed_turns.append((pending_user, normalized))
            pending_user = None

    history_turn_limit = max_history_messages // 2
    recent_history = [
        message
        for turn in completed_turns[-history_turn_limit:]
        for message in turn
    ] if history_turn_limit else []

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        *recent_history,
        {"role": "user", "content": prompt.strip()},
    ]
