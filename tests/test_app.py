import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from chat_logic import SYSTEM_PROMPT
from config import DEFAULT_BASE_URL, MODEL_NAME
from language_validator import AssameseLanguageValidator, LanguageDetectorError
from llama_cpp_client import LlamaCppClient


class FakeOllamaResponse:
    status_code = 200

    def __init__(self, content: str) -> None:
        self.content = content

    def json(self) -> dict[str, object]:
        return {
            "choices": [
                {
                    "message": {"content": self.content},
                    "finish_reason": "stop",
                }
            ],
        }

    def raise_for_status(self) -> None:
        return None


class FakeDetector:
    def predict(self, text: str) -> dict[str, object]:
        return {"lang": "assamese", "score": 0.99}


class StreamlitStartupTests(unittest.TestCase):
    def test_application_starts_when_the_selected_model_is_unavailable(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"

        validator = AssameseLanguageValidator(FakeDetector())
        with (
            patch("language_validator.get_language_validator", return_value=validator),
            patch.object(LlamaCppClient, "model_available", return_value=False),
        ):
            app = AppTest.from_file(str(app_path)).run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "অসমীয়া AI সহায়ক")
        self.assertIn("এই সহায়কে কেৱল অসমীয়া লিখনি গ্ৰহণ কৰে", app.info[0].value)
        visible_status = " ".join(
            item.value
            for collection in (app.caption, app.info, app.success, app.warning, app.error, app.markdown)
            for item in collection
            if isinstance(item.value, str)
        ).casefold()
        self.assertNotIn(MODEL_NAME.casefold(), visible_status)
        self.assertNotIn(DEFAULT_BASE_URL.casefold(), visible_status)
        self.assertNotIn("ollama", visible_status)
        self.assertNotIn("api", visible_status)

    def test_missing_language_model_displays_setup_error_without_traceback(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"

        with (
            patch(
                "language_validator.get_language_validator",
                side_effect=LanguageDetectorError("detector missing"),
            ),
            patch.object(LlamaCppClient, "model_available", return_value=False),
        ):
            app = AppTest.from_file(str(app_path)).run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertTrue(any("ভাষা পৰীক্ষক লোড কৰিব পৰা নগ'ল" in item.value for item in app.error))
        self.assertTrue(app.chat_input[0].disabled)

    def test_follow_up_request_contains_complete_ordered_chat_history(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        validator = AssameseLanguageValidator(FakeDetector())
        prompts = [
            "মোৰ নাম ৰাহুল। মই অষ্টম শ্ৰেণীত পঢ়োঁ আৰু বিজ্ঞান ভাল পাওঁ।",
            "মোৰ নাম কি? মই কোন শ্ৰেণীত পঢ়োঁ আৰু কোনটো বিষয় ভাল পাওঁ?",
        ]
        answers = iter(
            [
                "আপোনাক লগ পাই ভাল লাগিল, ৰাহুল।",
                "আপোনাৰ নাম ৰাহুল। আপুনি অষ্টম শ্ৰেণীত পঢ়ে আৰু বিজ্ঞান ভাল পায়।",
            ]
        )
        request_payloads: list[dict[str, object]] = []

        def fake_post(_url: str, *, json: dict[str, object], **_kwargs):
            request_payloads.append(json)
            return FakeOllamaResponse(next(answers))

        with (
            patch("language_validator.get_language_validator", return_value=validator),
            patch.object(LlamaCppClient, "model_available", return_value=True),
            patch("requests.Session.post", side_effect=fake_post),
        ):
            app = AppTest.from_file(str(app_path)).run(timeout=10)

            app.chat_input[0].set_value(prompts[0])
            app.run(timeout=10)
            app.chat_input[0].set_value(prompts[1])
            app.run(timeout=10)

            self.assertEqual(len(app.exception), 0)
            self.assertEqual(len(request_payloads), 2)
            self.assertEqual(
                request_payloads[1]["messages"],
                [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompts[0]},
                    {"role": "assistant", "content": "আপোনাক লগ পাই ভাল লাগিল, ৰাহুল।"},
                    {"role": "user", "content": prompts[1]},
                ],
            )
            self.assertEqual(
                [message["role"] for message in app.session_state["messages"]],
                ["user", "assistant", "user", "assistant"],
            )

            app.run(timeout=10)
            self.assertEqual(len(request_payloads), 2)

    def test_new_chat_clears_only_the_conversation_history(self) -> None:
        app_path = Path(__file__).resolve().parents[1] / "app.py"
        validator = AssameseLanguageValidator(FakeDetector())
        with (
            patch("language_validator.get_language_validator", return_value=validator),
            patch.object(LlamaCppClient, "model_available", return_value=True),
        ):
            app = AppTest.from_file(str(app_path)).run(timeout=10)
            app.session_state["messages"] = [
                {"role": "user", "content": "আগৰ প্ৰশ্ন"},
                {"role": "assistant", "content": "আগৰ উত্তৰ", "complete": True},
            ]
            app.session_state["unrelated_session_value"] = "preserved"
            app.run(timeout=10)
            new_chat = next(button for button in app.button if button.label == "New Chat")
            new_chat.click().run(timeout=10)

        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.session_state["messages"], [])
        self.assertEqual(app.session_state["unrelated_session_value"], "preserved")


if __name__ == "__main__":
    unittest.main()
