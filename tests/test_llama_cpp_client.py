import unittest
from unittest.mock import Mock

import requests

from config import AppConfig
from llama_cpp_client import LlamaCppChatResponse, LlamaCppClient
from ollama_client import (
    EmptyResponseError,
    ModelNotFoundError,
    OllamaResponseError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


class LlamaCppClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.session = Mock()
        self.client = LlamaCppClient(AppConfig(), session=self.session)

    @staticmethod
    def response(data: object, status_code: int = 200) -> Mock:
        response = Mock()
        response.status_code = status_code
        response.json.return_value = data
        if status_code >= 400:
            response.raise_for_status.side_effect = requests.HTTPError("request failed")
        return response

    def test_checks_health_and_the_exact_loaded_model_alias(self) -> None:
        self.session.get.side_effect = [
            self.response({"status": "ok"}),
            self.response({"data": [{"id": "assamese-q4-k-m"}]}),
        ]

        self.assertTrue(self.client.model_available())
        self.assertTrue(self.session.get.call_args_list[0].args[0].endswith("/health"))
        self.assertTrue(self.session.get.call_args_list[1].args[0].endswith("/v1/models"))

    def test_does_not_accept_an_unrelated_loaded_model(self) -> None:
        self.session.get.side_effect = [
            self.response({"status": "ok"}),
            self.response({"data": [{"id": "some-other-model"}]}),
        ]

        self.assertFalse(self.client.model_available())

    def test_sends_system_prompt_and_openai_chat_format(self) -> None:
        self.session.post.return_value = self.response(
            {"choices": [{"message": {"content": "মই ভালেই আছোঁ।"}, "finish_reason": "stop"}]}
        )

        answer = self.client.chat(
            [],
            "নমস্কাৰ! আপুনি কেনে আছে?",
            temperature=0.3,
            num_predict=96,
        )

        self.assertEqual(
            answer,
            LlamaCppChatResponse("মই ভালেই আছোঁ।", True, "stop"),
        )
        url = self.session.post.call_args.args[0]
        payload = self.session.post.call_args.kwargs["json"]
        self.assertTrue(url.endswith("/v1/chat/completions"))
        self.assertEqual(payload["model"], "assamese-q4-k-m")
        self.assertEqual(payload["messages"][0]["role"], "system")
        self.assertEqual(payload["messages"][-1]["content"], "নমস্কাৰ! আপুনি কেনে আছে?")
        self.assertEqual(payload["max_tokens"], 96)
        self.assertFalse(payload["stream"])

    def test_marks_length_limited_output_incomplete(self) -> None:
        self.session.post.return_value = self.response(
            {"choices": [{"message": {"content": "উত্তৰ অসম্পূৰ্ণ"}, "finish_reason": "length"}]}
        )

        self.assertFalse(self.client.chat([], "বুজাই দিয়ক").is_complete)

    def test_empty_content_is_an_error(self) -> None:
        self.session.post.return_value = self.response(
            {"choices": [{"message": {"content": " "}, "finish_reason": "stop"}]}
        )

        with self.assertRaises(EmptyResponseError):
            self.client.chat([], "নমস্কাৰ")

    def test_server_connection_and_timeout_are_reported(self) -> None:
        self.session.get.side_effect = requests.ConnectionError("refused")
        with self.assertRaises(OllamaUnavailableError):
            self.client.model_available()

        self.session.post.side_effect = requests.Timeout("timeout")
        with self.assertRaises(OllamaTimeoutError):
            self.client.chat([], "নমস্কাৰ")

    def test_model_not_found_is_reported(self) -> None:
        self.session.post.return_value = self.response(
            {"error": {"message": "model not found"}},
            status_code=404,
        )

        with self.assertRaises(ModelNotFoundError):
            self.client.chat([], "নমস্কাৰ")

    def test_malformed_completion_is_not_accepted(self) -> None:
        self.session.post.return_value = self.response({"choices": []})

        with self.assertRaises(OllamaResponseError):
            self.client.chat([], "নমস্কাৰ")


if __name__ == "__main__":
    unittest.main()
