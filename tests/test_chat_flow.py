import unittest

from chat_flow import (
    INCOMPLETE_ASSISTANT_MESSAGE,
    INVALID_ASSISTANT_MESSAGE,
    process_chat_turn,
)
from language_validator import AssameseLanguageValidator


class FakeDetector:
    def predict(self, text: str) -> dict[str, object]:
        if "Hello" in text or "English" in text:
            return {"lang": "english", "score": 0.99}
        if "বাংলা" in text:
            return {"lang": "bengali", "score": 0.99}
        if "English response" in text:
            return {"lang": "english", "score": 0.99}
        return {"lang": "assamese", "score": 0.95}


class FakeClient:
    def __init__(self, content: str, *, is_complete: bool = True) -> None:
        self.response = type(
            "FakeResponse",
            (),
            {"content": content, "is_complete": is_complete},
        )()
        self.calls: list[tuple[list[dict[str, object]], str]] = []

    def chat(self, history: list[dict[str, object]], prompt: str, **kwargs: object):
        self.calls.append((history.copy(), prompt))
        return self.response


class ChatFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = AssameseLanguageValidator(FakeDetector())
        self.options = {
            "temperature": 0.7,
            "num_predict": 1024,
            "history_messages": 12,
        }

    def test_rejected_input_never_reaches_model_or_conversation_history(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("উত্তৰ")

        result = process_chat_turn(
            "Hello, how are you?",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "input_rejected")
        self.assertEqual(result.message, "অনুগ্ৰহ কৰি কেৱল অসমীয়া ভাষাত প্ৰশ্ন লিখক।")
        self.assertEqual(client.calls, [])
        self.assertEqual(history, [])

    def test_bengali_input_never_reaches_model_or_history(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("অসমীয়া উত্তৰ")

        result = process_chat_turn(
            "বাংলা ভাষাৰ বাক্য",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "input_rejected")
        self.assertEqual(client.calls, [])
        self.assertEqual(history, [])

    def test_only_accepted_messages_and_valid_assamese_responses_enter_history(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("অসমীয়া ভাষা অতি সমৃদ্ধ।")

        result = process_chat_turn(
            "অসমীয়া ভাষাৰ বিষয়ে কওক।",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.response, "অসমীয়া ভাষা অতি সমৃদ্ধ।")
        self.assertEqual(
            history,
            [
                {"role": "user", "content": "অসমীয়া ভাষাৰ বিষয়ে কওক।"},
                {"role": "assistant", "content": "অসমীয়া ভাষা অতি সমৃদ্ধ।", "complete": True},
            ],
        )
        self.assertEqual(len(client.calls), 1)

    def test_safely_removes_think_block_before_output_validation(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("<think>private reasoning</think> অসমীয়া ভাষা সমৃদ্ধ।")

        result = process_chat_turn(
            "অসমীয়া ভাষাৰ বিষয়ে কওক।",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "accepted")
        self.assertEqual(result.response, "অসমীয়া ভাষা সমৃদ্ধ।")
        self.assertNotIn("<think>", result.response)

    def test_non_assamese_output_is_not_displayed_or_stored(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("English response")

        result = process_chat_turn(
            "অসমীয়া ভাষাৰ বিষয়ে কওক।",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "output_rejected")
        self.assertEqual(result.message, INVALID_ASSISTANT_MESSAGE)
        self.assertIsNone(result.response)
        self.assertEqual(history, [])

    def test_unmatched_internal_tag_does_not_get_displayed_or_stored(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("<think>reasoning without a closing tag")

        result = process_chat_turn(
            "অসমীয়া ভাষাৰ বিষয়ে কওক।",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "output_rejected")
        self.assertEqual(result.message, INVALID_ASSISTANT_MESSAGE)
        self.assertEqual(history, [])

    def test_incomplete_response_is_not_displayed_or_stored(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("অসম্পূৰ্ণ উত্তৰ", is_complete=False)

        result = process_chat_turn(
            "অসমীয়া ভাষাৰ বিষয়ে কওক।",
            history,
            self.validator,
            client,
            **self.options,
        )

        self.assertEqual(result.status, "incomplete")
        self.assertEqual(result.message, INCOMPLETE_ASSISTANT_MESSAGE)
        self.assertIsNone(result.response)
        self.assertEqual(history, [])

    def test_odd_history_limit_retains_only_complete_turns(self) -> None:
        history: list[dict[str, object]] = []
        client = FakeClient("উত্তৰ ১।")
        for index in range(1, 4):
            client.response.content = f"উত্তৰ {index}।"
            process_chat_turn(
                f"প্ৰশ্ন {index}",
                history,
                self.validator,
                client,
                **{**self.options, "history_messages": 3},
            )

        self.assertEqual(
            history,
            [
                {"role": "user", "content": "প্ৰশ্ন 3"},
                {"role": "assistant", "content": "উত্তৰ 3।", "complete": True},
            ],
        )


if __name__ == "__main__":
    unittest.main()
