import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Protocol, Sequence


ASSAMESE_LANGUAGE = "assamese"
ASSAMESE_ONLY_MESSAGE = "অনুগ্ৰহ কৰি কেৱল অসমীয়া ভাষাত প্ৰশ্ন লিখক।"
MIN_LANGUAGE_CONFIDENCE = 0.75
MIN_LETTER_COUNT = 4
INDICLID_REPOSITORY = "ai4bharat/IndicLID-FTN"
INDICLID_REVISION = "68c6f11c13174d7f2e734012f2d1cad4449254ae"
INDICLID_MODEL_FILE = "model_baseline_roman.bin"


class LanguageDetector(Protocol):
    def predict(self, text: str) -> dict[str, object]: ...


class LanguageDetectorError(RuntimeError):
    """Raised when the local language identification model is unavailable or invalid."""


class _FastTextModel(Protocol):
    def predict(self, text: str, k: int = 1) -> tuple[Sequence[str], Sequence[float]]: ...


LANGUAGE_CODES = {
    "asm": "assamese",
    "ben": "bengali",
    "eng": "english",
    "hin": "hindi",
}

ENGLISH_MARKERS = frozenset(
    {
        "a", "an", "the", "and", "or", "but", "if", "is", "are", "was", "were",
        "be", "been", "being", "have", "has", "had", "do", "does", "did", "can",
        "could", "will", "would", "should", "may", "might", "must", "this", "that",
        "these", "those", "it", "he", "she", "they", "we", "you", "your", "yours",
        "i", "my", "me", "mine", "please", "thanks", "thank", "hello", "hi", "hey",
        "ok", "okay", "sure", "sorry", "goodbye", "bye", "good", "morning", "what",
        "when", "where", "why", "who", "how", "which", "explain", "tell", "about",
        "in", "on", "for", "to", "from", "with", "without", "not", "no", "yes",
        "want", "need", "give", "help", "write", "answer", "only", "name",
        "assistant", "language",
    }
)
TECHNICAL_LATIN_ALLOWLIST = frozenset(
    {
        "ai", "api", "cpu", "gpu", "ram", "url", "http", "https", "json", "llm",
        "python", "streamlit", "chatbot", "ollama", "fasttext", "indiclid",
        "windows", "chatgpt", "openai",
    }
)
LATIN_WORD_PATTERN = re.compile(r"[A-Za-z]+(?:['’][A-Za-z]+)?")
CODE_OR_URL_PATTERN = re.compile(
    r"```.*?```|`[^`]*`|https?://\S+",
    re.IGNORECASE | re.DOTALL,
)


class IndicLIDDetector:
    def __init__(self, model: _FastTextModel) -> None:
        self.model = model

    def predict(self, text: str) -> dict[str, object]:
        normalized = " ".join(text.splitlines())
        labels, scores = self.model.predict(normalized, k=2)
        if len(labels) == 0 or len(scores) == 0:
            raise LanguageDetectorError("IndicLID returned no language prediction.")

        raw_label = labels[0].removeprefix("__label__")
        language_code = raw_label.split("_", maxsplit=1)[0].casefold()
        language = LANGUAGE_CODES.get(language_code, raw_label)
        confidence = min(1.0, max(0.0, float(scores[0])))
        return {"lang": language, "label": raw_label, "score": confidence}


@dataclass(frozen=True)
class LanguageDecision:
    accepted: bool
    language: str | None
    confidence: float | None
    reason: str | None = None
    label: str | None = None


class AssameseLanguageValidator:
    def __init__(
        self,
        detector: LanguageDetector,
        *,
        min_confidence: float = MIN_LANGUAGE_CONFIDENCE,
        min_letter_count: int = MIN_LETTER_COUNT,
    ) -> None:
        if not 0.0 < min_confidence <= 1.0:
            raise ValueError("min_confidence must be greater than 0 and at most 1.")
        if min_letter_count < 1:
            raise ValueError("min_letter_count must be at least 1.")
        self.detector = detector
        self.min_confidence = min_confidence
        self.min_letter_count = min_letter_count

    def validate(self, text: str) -> LanguageDecision:
        normalized = text.strip()
        if not normalized:
            return LanguageDecision(False, None, None, "empty")

        if sum(character.isalpha() for character in normalized) < self.min_letter_count:
            return LanguageDecision(False, None, None, "too_short_or_not_language_text")

        if _contains_english_marker(normalized):
            return LanguageDecision(False, "mixed", None, "mixed_language_marker")

        try:
            prediction = self.detector.predict(normalized)
        except Exception as error:
            raise LanguageDetectorError("The local Assamese language detector failed.") from error

        if not isinstance(prediction, dict):
            raise LanguageDetectorError("The local language detector returned an invalid result.")
        language = prediction.get("lang")
        label = prediction.get("label")
        confidence = prediction.get("score")
        if (
            not isinstance(language, str)
            or (label is not None and not isinstance(label, str))
            or not isinstance(confidence, (int, float))
            or isinstance(confidence, bool)
            or not 0.0 <= float(confidence) <= 1.0
        ):
            raise LanguageDetectorError("The local language detector returned an invalid label or score.")

        confidence = float(confidence)
        is_assamese_script = label is None or label.casefold() == "asm_beng"
        accepted = (
            language.casefold() == ASSAMESE_LANGUAGE
            and is_assamese_script
            and confidence >= self.min_confidence
        )
        reason = None if accepted else "language_not_confidently_assamese"
        return LanguageDecision(accepted, language, confidence, reason, label)


def _contains_english_marker(text: str) -> bool:
    without_code = CODE_OR_URL_PATTERN.sub(" ", text)
    for word in LATIN_WORD_PATTERN.findall(without_code):
        normalized = word.casefold()
        if normalized in ENGLISH_MARKERS and normalized not in TECHNICAL_LATIN_ALLOWLIST:
            return True
    return False


@lru_cache(maxsize=1)
def get_language_validator() -> AssameseLanguageValidator:
    try:
        import fasttext
        from huggingface_hub import hf_hub_download

        model_path = hf_hub_download(
            repo_id=INDICLID_REPOSITORY,
            filename=INDICLID_MODEL_FILE,
            revision=INDICLID_REVISION,
        )
        detector = IndicLIDDetector(fasttext.load_model(str(Path(model_path))))
    except Exception as error:
        raise LanguageDetectorError(
            "Could not load the local IndicLID model. Install the project requirements and check "
            "access to the Hugging Face model cache or network for its first download."
        ) from error
    return AssameseLanguageValidator(detector)
