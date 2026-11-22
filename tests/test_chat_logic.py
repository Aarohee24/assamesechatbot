import unittest

from chat_logic import SYSTEM_PROMPT, build_messages, sanitize_assistant_response


class BuildMessagesTests(unittest.TestCase):
    def test_prepends_the_persistent_identity_instruction(self) -> None:
        messages = build_messages([], "আপুনি কোন?", max_history_messages=12)

        self.assertEqual(
            messages[0],
            {
                "role": "system",
                "content": (
                    "You are অসমীয়া AI সহায়ক, an assistant that communicates only in Assamese. "
                    "Every user message reaching you has already passed Assamese-language validation. "
                    "Answer only in natural Assamese, using Assamese script. Do not answer in English, "
                    "Hindi, Bengali, or any other language. Do not identify yourself as ChatGPT. If asked "
                    "your identity, introduce yourself as অসমীয়া AI সহায়ক. Use complete sentences, "
                    "answer the user's question directly, and acknowledge uncertainty when needed. "
                    "Do not reveal internal reasoning or emit <think> tags."
                ),
            },
        )

    def test_builds_system_history_and_current_prompt(self) -> None:
        history = [
            {"role": "user", "content": "আগৰ প্ৰশ্ন"},
            {"role": "assistant", "content": "আগৰ উত্তৰ"},
        ]

        messages = build_messages(history, "  নতুন প্ৰশ্ন  ", max_history_messages=2)

        self.assertEqual(messages[0], {"role": "system", "content": SYSTEM_PROMPT})
        self.assertEqual(messages[1:], history + [{"role": "user", "content": "নতুন প্ৰশ্ন"}])

    def test_keeps_only_the_most_recent_complete_turns(self) -> None:
        history = []
        for index in range(3):
            history.extend(
                [
                    {"role": "user", "content": f"প্ৰশ্ন {index}"},
                    {"role": "assistant", "content": f"উত্তৰ {index}"},
                ]
            )

        messages = build_messages(history, "নতুন", max_history_messages=2)

        self.assertEqual(messages[1:], history[-2:] + [{"role": "user", "content": "নতুন"}])

    def test_excludes_invalid_history_entries(self) -> None:
        history = [
            {"role": "system", "content": "old system"},
            {"role": "user", "content": "valid question"},
            {"role": "assistant", "content": "valid answer"},
        ]

        messages = build_messages(history, "প্ৰশ্ন", max_history_messages=4)

        self.assertEqual(messages[1:], history[1:] + [{"role": "user", "content": "প্ৰশ্ন"}])

    def test_rejects_empty_prompt(self) -> None:
        with self.assertRaisesRegex(ValueError, "empty"):
            build_messages([], "  ", max_history_messages=2)

    def test_zero_history_limit_sends_no_prior_messages(self) -> None:
        messages = build_messages(
            [{"role": "user", "content": "আগৰ কথা"}],
            "নতুন কথা",
            max_history_messages=0,
        )

        self.assertEqual(len(messages), 2)

    def test_odd_history_limit_does_not_send_half_a_turn(self) -> None:
        history = [
            {"role": "user", "content": "প্ৰশ্ন"},
            {"role": "assistant", "content": "উত্তৰ"},
        ]

        messages = build_messages(history, "নতুন", max_history_messages=1)

        self.assertEqual(messages[1:], [{"role": "user", "content": "নতুন"}])

    def test_excludes_incomplete_turns_from_future_context(self) -> None:
        history = [
            {"role": "user", "content": "আগৰ প্ৰশ্ন"},
            {"role": "assistant", "content": "অসম্পূৰ্ণ উত্তৰ", "complete": False},
        ]

        messages = build_messages(history, "নতুন প্ৰশ্ন", max_history_messages=12)

        self.assertEqual(messages[1:], [{"role": "user", "content": "নতুন প্ৰশ্ন"}])

    def test_strips_a_complete_private_think_block(self) -> None:
        self.assertEqual(
            sanitize_assistant_response("<think>private reasoning</think> অসমীয়া উত্তৰ।"),
            "অসমীয়া উত্তৰ।",
        )

    def test_rejects_unmatched_internal_tags_and_empty_final_text(self) -> None:
        self.assertIsNone(sanitize_assistant_response("<think>private reasoning"))
        self.assertIsNone(sanitize_assistant_response("<think>private reasoning</think>"))
        self.assertIsNone(sanitize_assistant_response("<|im_start|>assistant"))


if __name__ == "__main__":
    unittest.main()
