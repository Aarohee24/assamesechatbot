import unittest
from unittest.mock import Mock

import requests

from config import AppConfig
from ollama_client import (
    EmptyResponseError,
    ModelNotFoundError,
    OllamaClient,
    OllamaChatResponse,
    OllamaResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


class OllamaClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.client = OllamaClient(AppConfig(), session=self.session)

    @staticmethod
    def response(data: object, status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data
        if status_code >= 400:
            response.raise_for_status.side_effect = requests.HTTPError("request failed")
        return response

    def test_sends_selected_model_and_supported_chat_format(self) -> None:
        self.session.post.return_value = self.response(
            {"message": {"content": "মই ভালেই আছোঁ।"}}
        )

        answer = self.client.chat(
            [{"role": "user", "content": "নমস্কাৰ"}],
            "আপুনি কেনে আছে?",
            temperature=0.4,
            num_predict=128,
        )

        self.assertEqual(answer, OllamaChatResponse("মই ভালেই আছোঁ।", None, None))
        kwargs = self.session.post.call_args.kwargs
        self.assertEqual(kwargs["json"]["model"], AppConfig().model_name)
        self.assertEqual(kwargs["json"]["messages"][0]["role"], "system")
        self.assertIn("Do not identify yourself as ChatGPT.", kwargs["json"]["messages"][0]["content"])
        self.assertIn("communicates only in Assamese", kwargs["json"]["messages"][0]["content"])
        self.assertEqual(kwargs["json"]["messages"][-1]["content"], "আপুনি কেনে আছে?")
        self.assertFalse(kwargs["json"]["stream"])
        self.assertEqual(kwargs["json"]["options"], {"temperature": 0.4, "num_predict": 128})
        self.assertFalse(kwargs["json"]["think"])
        self.assertFalse(kwargs["allow_redirects"])
        self.assertIn("/api/chat", self.session.post.call_args.args[0])

    def test_uses_the_configured_default_generation_limit(self) -> None:
        self.session.post.return_value = self.response(
            {"message": {"content": "উত্তৰ"}, "done": True, "done_reason": "stop"}
        )

        self.client.chat([], "নমস্কাৰ")

        payload = self.session.post.call_args.kwargs["json"]
        self.assertEqual(payload["options"]["num_predict"], 512)
        self.assertEqual(payload["messages"][0]["role"], "system")

    def test_preserves_ollama_completion_metadata(self) -> None:
        self.session.post.return_value = self.response(
            {
                "message": {"content": "সম্পূৰ্ণ উত্তৰ।"},
                "done": True,
                "done_reason": "stop",
            }
        )

        response = self.client.chat([], "নমস্কাৰ")

        self.assertTrue(response.is_complete)
        self.assertTrue(response.done)
        self.assertEqual(response.done_reason, "stop")

    def test_marks_a_length_limited_response_incomplete(self) -> None:
        self.session.post.return_value = self.response(
            {
                "message": {"content": "উত্তৰ ইয়াতেই থামিল"},
                "done": True,
                "done_reason": "length",
            }
        )

        response = self.client.chat([], "পাঁচটা বাক্য লিখক")

        self.assertEqual(response.content, "উত্তৰ ইয়াতেই থামিল")
        self.assertFalse(response.is_complete)

    def test_marks_a_response_with_done_false_incomplete(self) -> None:
        self.session.post.return_value = self.response(
            {
                "message": {"content": "অসম্পূৰ্ণ উত্তৰ"},
                "done": False,
            }
        )

        self.assertFalse(self.client.chat([], "প্ৰশ্ন").is_complete)

    def test_empty_input_is_rejected_before_http_request(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            self.client.chat([], "  ")
        self.session.post.assert_not_called()

    def test_reports_unavailable_ollama_service(self) -> None:
        self.session.post.side_effect = requests.ConnectionError("connection refused")

        with self.assertRaises(OllamaUnavailableError):
            self.client.chat([], "নমস্কাৰ")

    def test_reports_generation_timeout_separately(self) -> None:
        self.session.post.side_effect = requests.Timeout("read timed out")

        with self.assertRaisesRegex(OllamaTimeoutError, "300 seconds"):
            self.client.chat([], "নমস্কাৰ")

    def test_reports_missing_model(self) -> None:
        self.session.post.return_value = self.response(
            {"error": "model not found"},
            status_code=404,
        )

        with self.assertRaises(ModelNotFoundError):
            self.client.chat([], "নমস্কাৰ")

    def test_rejects_redirects_instead_of_following_them(self) -> None:
        self.session.post.return_value = self.response({}, status_code=307)

        with self.assertRaisesRegex(OllamaResponseError, "redirect"):
            self.client.chat([], "নমস্কাৰ")

    def test_reports_malformed_response(self) -> None:
        response = self.response({})
        response.json.side_effect = ValueError("invalid json")
        self.session.post.return_value = response

        with self.assertRaises(OllamaResponseError):
            self.client.chat([], "নমস্কাৰ")

    def test_reports_empty_model_response(self) -> None:
        self.session.post.return_value = self.response({"message": {"content": "  "}})

        with self.assertRaises(EmptyResponseError):
            self.client.chat([], "নমস্কাৰ")

    def test_checks_exact_installed_model_name(self) -> None:
        self.session.get.return_value = self.response(
            {"models": [{"name": AppConfig().model_name}]}
        )

        self.assertTrue(self.client.model_available())
        self.assertIn("/api/tags", self.session.get.call_args.args[0])

    def test_lists_models_without_matching_a_different_tag(self) -> None:
        self.session.get.return_value = self.response(
            {"models": [{"name": "another/model:latest"}]}
        )

        self.assertFalse(self.client.model_available())


if __name__ == "__main__":
    unittest.main()
