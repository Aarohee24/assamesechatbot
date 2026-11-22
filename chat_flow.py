from dataclasses import dataclass
from typing import Protocol

from chat_logic import sanitize_assistant_response
from language_validator import (
    ASSAMESE_ONLY_MESSAGE,
    AssameseLanguageValidator,
    LanguageDecision,
)


INVALID_ASSISTANT_MESSAGE = "ক্ষমা কৰিব, উত্তৰটো অসমীয়াত নিশ্চিত কৰিব নোৱাৰিলোঁ। অনুগ্ৰহ কৰি আকৌ প্ৰশ্ন কৰক।"
INCOMPLETE_ASSISTANT_MESSAGE = "ক্ষমা কৰিব, সম্পূৰ্ণ অসমীয়া উত্তৰ পোৱা নগ'ল। অনুগ্ৰহ কৰি আকৌ প্ৰশ্ন কৰক।"


class ChatResponse(Protocol):
    content: str
    is_complete: bool


class ChatClient(Protocol):
    def chat(
        self,
        history: list[dict[str, object]],
        prompt: str,
        *,
        temperature: float | None = None,
        num_predict: int | None = None,
        history_messages: int | None = None,
    ) -> ChatResponse: ...


@dataclass(frozen=True)
class ChatTurnResult:
    status: str
    message: str | None = None
    response: str | None = None
    input_decision: LanguageDecision | None = None
    output_decision: LanguageDecision | None = None


def process_chat_turn(
    prompt: str,
    history: list[dict[str, object]],
    validator: AssameseLanguageValidator,
    client: ChatClient,
    *,
    temperature: float,
    num_predict: int,
    history_messages: int,
) -> ChatTurnResult:
    input_decision = validator.validate(prompt)
    if not input_decision.accepted:
        return ChatTurnResult("input_rejected", ASSAMESE_ONLY_MESSAGE, input_decision=input_decision)

    model_response = client.chat(
        history,
        prompt,
        temperature=temperature,
        num_predict=num_predict,
        history_messages=history_messages,
    )
    if not model_response.is_complete:
        return ChatTurnResult(
            "incomplete",
            INCOMPLETE_ASSISTANT_MESSAGE,
            input_decision=input_decision,
        )

    sanitized = sanitize_assistant_response(model_response.content)
    if sanitized is None:
        return ChatTurnResult(
            "output_rejected",
            INVALID_ASSISTANT_MESSAGE,
            input_decision=input_decision,
        )

    output_decision = validator.validate(sanitized)
    if not output_decision.accepted:
        return ChatTurnResult(
            "output_rejected",
            INVALID_ASSISTANT_MESSAGE,
            input_decision=input_decision,
            output_decision=output_decision,
        )

    history.extend(
        [
            {"role": "user", "content": prompt.strip()},
            {"role": "assistant", "content": sanitized, "complete": True},
        ]
    )
    history_turn_limit = history_messages // 2
    if history_turn_limit:
        del history[: -(history_turn_limit * 2)]
    else:
        history.clear()
    return ChatTurnResult(
        "accepted",
        response=sanitized,
        input_decision=input_decision,
        output_decision=output_decision,
    )
