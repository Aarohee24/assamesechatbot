from dataclasses import dataclass

import requests

from chat_logic import build_messages
from config import AppConfig


class OllamaError(Exception):
    """Base error for problems communicating with the local Ollama service."""


class OllamaUnavailableError(OllamaError):
    """Raised when the local Ollama API cannot be reached."""


class OllamaTimeoutError(OllamaError):
    """Raised when a local Ollama request exceeds its configured timeout."""


class ModelNotFoundError(OllamaError):
    """Raised when the selected model is not installed in Ollama."""


class OllamaResponseError(OllamaError):
    """Raised when Ollama returns an invalid or unsuccessful response."""


class EmptyResponseError(OllamaResponseError):
    """Raised when the model returns no message content."""


@dataclass(frozen=True)
class OllamaChatResponse:
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


class OllamaClient:
    def __init__(self, config: AppConfig, session: requests.Session | None = None) -> None:
        self.config = config
        self.session = session or requests.Session()
        self.session.trust_env = False

    def list_models(self) -> list[str]:
        try:
            response = self.session.get(
                f"{self.config.base_url}/api/tags",
                timeout=(3, 5),
                allow_redirects=False,
            )
        except requests.Timeout as error:
            raise OllamaTimeoutError("Timed out while checking the local Ollama service.") from error
        except requests.ConnectionError as error:
            raise OllamaUnavailableError(
                "Could not reach Ollama at the configured local address. Start Ollama and try again."
            ) from error

        if 300 <= response.status_code < 400:
            raise OllamaResponseError("Ollama returned an unexpected redirect; only the local API is allowed.")

        data = self._decode_response(response)
        models = data.get("models")
        if not isinstance(models, list):
            raise OllamaResponseError("Ollama returned an unexpected model-list response.")

        names: list[str] = []
        for model in models:
            if not isinstance(model, dict) or not isinstance(model.get("name"), str):
                raise OllamaResponseError("Ollama returned a malformed model entry.")
            names.append(model["name"])
        return names

    def model_available(self) -> bool:
        return self.config.model_name in self.list_models()

    def chat(
        self,
        history: list[dict[str, object]],
        prompt: str,
        *,
        temperature: float | None = None,
        num_predict: int | None = None,
        history_messages: int | None = None,
    ) -> OllamaChatResponse:
        messages = build_messages(
            history,
            prompt,
            self.config.history_messages if history_messages is None else history_messages,
        )
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {
                "temperature": self.config.temperature if temperature is None else temperature,
                "num_predict": self.config.num_predict if num_predict is None else num_predict,
            },
        }

        try:
            response = self.session.post(
                f"{self.config.base_url}/api/chat",
                json=payload,
                timeout=(5, self.config.request_timeout),
                allow_redirects=False,
            )
        except requests.Timeout as error:
            raise OllamaTimeoutError(
                f"Ollama did not finish within {self.config.request_timeout:g} seconds. "
                "Try again or reduce the response length."
            ) from error
        except requests.ConnectionError as error:
            raise OllamaUnavailableError(
                "Could not reach Ollama at the configured local address. Check that Ollama is running."
            ) from error

        if response.status_code == 404:
            raise ModelNotFoundError(
                f"Model '{self.config.model_name}' was not found. Pull that exact model in Ollama and retry."
            )
        if 300 <= response.status_code < 400:
            raise OllamaResponseError("Ollama returned an unexpected redirect; only the local API is allowed.")

        data = self._decode_response(response)
        if isinstance(data.get("error"), str):
            error_message = data["error"]
            if "not found" in error_message.lower() and "model" in error_message.lower():
                raise ModelNotFoundError(
                    f"Model '{self.config.model_name}' is not installed. Pull that exact model and retry."
                )
            raise OllamaResponseError(f"Ollama reported an error: {error_message}")

        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise OllamaResponseError("Ollama returned a response without message content.")
        if not content.strip():
            raise EmptyResponseError("The model returned an empty response. Please try again.")
        done = data.get("done")
        if done is not None and not isinstance(done, bool):
            raise OllamaResponseError("Ollama returned an invalid completion status.")
        done_reason = data.get("done_reason")
        if done_reason is not None and not isinstance(done_reason, str):
            raise OllamaResponseError("Ollama returned an invalid completion reason.")
        return OllamaChatResponse(content.strip(), done, done_reason)

    @staticmethod
    def _decode_response(response: requests.Response) -> dict[str, object]:
        try:
            response.raise_for_status()
        except requests.HTTPError as error:
            raise OllamaResponseError(
                f"Ollama returned HTTP {response.status_code}. Check the local Ollama service."
            ) from error

        try:
            data = response.json()
        except ValueError as error:
            raise OllamaResponseError("Ollama returned malformed JSON.") from error
        if not isinstance(data, dict):
            raise OllamaResponseError("Ollama returned an unexpected response format.")
        return data
