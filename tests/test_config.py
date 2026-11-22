import unittest
from unittest.mock import patch

from config import AppConfig, MODEL_NAME


class AppConfigTests(unittest.TestCase):
    def test_defaults_select_the_requested_local_model(self) -> None:
        config = AppConfig()

        self.assertEqual(config.base_url, "http://127.0.0.1:8081")
        self.assertEqual(config.model_name, MODEL_NAME)
        self.assertEqual(config.num_predict, 512)
        self.assertEqual(config.history_messages, 4)

    def test_rejects_non_local_api_url(self) -> None:
        with self.assertRaisesRegex(ValueError, "local HTTP URL"):
            AppConfig(base_url="https://example.com")

    def test_rejects_invalid_generation_settings(self) -> None:
        with self.assertRaisesRegex(ValueError, "TEMPERATURE"):
            AppConfig(temperature=2.1)
        with self.assertRaisesRegex(ValueError, "at least 1"):
            AppConfig(num_predict=0)
        with self.assertRaisesRegex(ValueError, "TIMEOUT"):
            AppConfig(request_timeout=float("nan"))

    def test_loads_settings_from_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "LLAMA_CPP_BASE_URL": "http://127.0.0.1:8081/",
                "LLAMA_CPP_TEMPERATURE": "0.5",
                "LLAMA_CPP_NUM_PREDICT": "192",
                "CHAT_HISTORY_MESSAGES": "8",
            },
            clear=True,
        ):
            config = AppConfig.from_env()

        self.assertEqual(config.base_url, "http://127.0.0.1:8081")
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.num_predict, 192)
        self.assertEqual(config.history_messages, 8)

    def test_environment_default_matches_app_generation_limit(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            config = AppConfig.from_env()

        self.assertEqual(config.num_predict, 512)

    def test_reports_invalid_environment_values(self) -> None:
        with patch.dict("os.environ", {"LLAMA_CPP_TEMPERATURE": "invalid"}, clear=True):
            with self.assertRaisesRegex(ValueError, "Invalid chatbot configuration"):
                AppConfig.from_env()


if __name__ == "__main__":
    unittest.main()
