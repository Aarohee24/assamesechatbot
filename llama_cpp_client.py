from dataclasses import dataclass

import requests

from chat_logic import build_messages
from config import AppConfig
from ollama_client import (
    EmptyResponseError,
    ModelNotFoundError,
    OllamaError,
    OllamaResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


@dataclass(frozen=True)
class LlamaCppChatResponse:
    content: str
    done: bool | None
    done_reason: str | None

    @property
    def is_complete(self) -> bool:
        return self.done is not False and (self.done_reason or "").casefold() not in {
            "length",
            "limit",
            "max_tokens",
            "token_limit",
        }


class LlamaCppClient:
    def __init__(
        self, config: AppConfig, session: requests.Session | None = None
    ) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.session.trust_env = False

    def model_available(self) -> bool:
        try:
            response = self.session.get(
                f"{self.config.base_url}/health",
                timeout=(3, 5),
                allow_redirects=False,
            )
        except requests.Timeout as error:
            raise OllamaTimeoutError(
                "Timed out while checking the local llama.cpp server."
            ) from error
        except requests.ConnectionError as error:
            raise OllamaUnavailableError(
                "Could not reach the local llama.cpp server. Start the chatbot launcher and retry."
            ) from error

        data = self._decode_response(response, "llama.cpp health")
        status = data.get("status")
        if status != "ok":
            return False

        models_response = self._get_models()
        models = models_response.get("data")
        if not isinstance(models, list):
            raise OllamaResponseError(
                "llama.cpp returned an unexpected model-list response."
            )
        names = [
            item.get("id")
            for item in models
            if isinstance(item, dict) and isinstance(item.get("id"), str)
        ]
        return self.config.model_name in names

    def _get_models(self) -> dict[str, object]:
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/models",
                timeout=(3, 5),
                allow_redirects=False,
            )
        except requests.Timeout as error:
            raise OllamaTimeoutError(
                "Timed out while checking the loaded local GGUF model."
            ) from error
        except requests.ConnectionError as error:
            raise OllamaUnavailableError(
                "Could not reach the local llama.cpp server."
            ) from error
        return self._decode_response(response, "llama.cpp model list")

    def chat(
        self,
        history: list[dict[str, object]],
        prompt: str,
        *,
        temperature: float | None = None,
        num_predict: int | None = None,
        history_messages: int | None = None,
    ) -> LlamaCppChatResponse:
        messages = build_messages(
            history,
            prompt,
            self.config.history_messages
            if history_messages is None
            else history_messages,
        )
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "temperature": (
                self.config.temperature if temperature is None else temperature
            ),
            "max_tokens": (
                self.config.num_predict if num_predict is None else num_predict
            ),
        }

        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/chat/completions",
                json=payload,
                timeout=(5, self.config.request_timeout),
                allow_redirects=False,
            )
        except requests.Timeout as error:
            raise OllamaTimeoutError(
                f"llama.cpp did not finish within {self.config.request_timeout:g} seconds. "
                "Try again or reduce the response length."
            ) from error
        except requests.ConnectionError as error:
            raise OllamaUnavailableError(
                "Could not reach the local llama.cpp server. Check that the GGUF runtime is running."
            ) from error

        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Loaded GGUF alias '{self.config.model_name}' was not found by llama.cpp."
            )
        if 300 <= response.status_code < 400:
            raise OllamaResponseError(
                "llama.cpp returned an unexpected redirect; only the local API is allowed."
            )

        data = self._decode_response(response, "llama.cpp chat")
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise OllamaResponseError(
                "llama.cpp returned a response without a chat completion choice."
            )
        choice = choices[0]
        message = choice.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise OllamaResponseError(
                "llama.cpp returned a completion without message content."
            )
        if not content.strip():
            raise EmptyResponseError("The model returned an empty response. Please try again.")

        finish_reason = choice.get("finish_reason")
        if finish_reason is not None and not isinstance(finish_reason, str):
            raise OllamaResponseError("llama.cpp returned an invalid finish reason.")
        is_complete = finish_reason not in {"length", "content_filter"}
        return LlamaCppChatResponse(content.strip(), is_complete, finish_reason)

    @staticmethod
    def _decode_response(
        response: requests.Response, endpoint: str
    ) -> dict[str, object]:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise OllamaResponseError(
                f"{endpoint} returned HTTP {response.status_code}."
            ) from error
        try:
            data = response.json()
        except ValueError as error:
            raise OllamaResponseError(
                f"{endpoint} returned malformed JSON."
            ) from error
        if not isinstance(data, dict):
            raise OllamaResponseError(
                f"{endpoint} returned an unexpected response format."
            )
        error_message = data.get("error")
        if isinstance(error_message, str):
            raise OllamaResponseError(
                f"llama.cpp reported an error: {error_message}"
            )
        return data
