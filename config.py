import math
import os
from dataclasses import dataclass
from urllib.parse import urlsplit


MODEL_NAME = "assamese-q4-k-m"
DEFAULT_BASE_URL = "http://127.0.0.1:8081"


@dataclass(frozen=True)
class AppConfig:
    base_url: str = DEFAULT_BASE_URL
    model_name: str = MODEL_NAME
    temperature: float = 0.7
    num_predict: int = 512
    history_messages: int = 4
    request_timeout: float = 300.0

    def __post_init__(self) -> None:
        parsed_url = urlsplit(self.base_url)
        try:
            port = parsed_url.port
        except ValueError as error:
            raise ValueError("LLAMA_CPP_BASE_URL contains an invalid port.") from error
        if (
            parsed_url.scheme != "http"
            or parsed_url.hostname not in {"localhost", "127.0.0.1", "::1"}
            or parsed_url.username is not None
            or parsed_url.password is not None
            or parsed_url.path not in {"", "/"}
            or parsed_url.query
            or parsed_url.fragment
            or port == 0
        ):
            raise ValueError(
                "LLAMA_CPP_BASE_URL must be a local HTTP URL, such as http://127.0.0.1:8081."
            )
        if not self.model_name.strip():
            raise ValueError("LLAMA_CPP_MODEL must not be empty.")
        if not math.isfinite(self.temperature) or not 0.0 <= self.temperature <= 2.0:
            raise ValueError("LLAMA_CPP_TEMPERATURE must be between 0 and 2.")
        if self.num_predict < 1:
            raise ValueError("LLAMA_CPP_NUM_PREDICT must be at least 1.")
        if self.history_messages < 0:
            raise ValueError("CHAT_HISTORY_MESSAGES must not be negative.")
        if not math.isfinite(self.request_timeout) or self.request_timeout <= 0:
            raise ValueError("LLAMA_CPP_TIMEOUT_SECONDS must be greater than 0.")

        object.__setattr__(self, "base_url", self.base_url.rstrip("/"))

    @classmethod
    def from_env(cls) -> "AppConfig":
        try:
            return cls(
                base_url=os.getenv("LLAMA_CPP_BASE_URL", DEFAULT_BASE_URL),
                model_name=os.getenv("LLAMA_CPP_MODEL", MODEL_NAME),
                temperature=float(os.getenv("LLAMA_CPP_TEMPERATURE", "0.7")),
                num_predict=int(os.getenv("LLAMA_CPP_NUM_PREDICT", "512")),
                history_messages=int(os.getenv("CHAT_HISTORY_MESSAGES", "4")),
                request_timeout=float(os.getenv("LLAMA_CPP_TIMEOUT_SECONDS", "300")),
            )
        except ValueError as error:
            raise ValueError(f"Invalid chatbot configuration: {error}") from error
