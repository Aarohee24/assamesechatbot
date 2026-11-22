import unittest

from language_validator import (
    MIN_LANGUAGE_CONFIDENCE,
    AssameseLanguageValidator,
    IndicLIDDetector,
)


class FakeFastTextModel:
    def __init__(self, label: str, score: float) -> None:
        self.label = label
        self.score = score
        self.calls: list[tuple[str, int]] = []

    def predict(self, text: str, k: int = 1) -> tuple[list[str], list[float]]:
        self.calls.append((text, k))
        return [f"__label__{self.label}"], [self.score]


class FakeDetector:
    def __init__(self, language: str, score: float) -> None:
        self.language = language
        self.score = score
        self.calls: list[str] = []

    def predict(self, text: str) -> dict[str, object]:
        self.calls.append(text)
        return {"lang": self.language, "score": self.score}


class IndicLIDAdapterTests(unittest.TestCase):
    def test_maps_assamese_and_bengali_script_labels_distinctly(self) -> None:
        assamese_model = FakeFastTextModel("asm_Beng", 0.96)
        bengali_model = FakeFastTextModel("ben_Beng", 0.98)

        assamese = IndicLIDDetector(assamese_model).predict("অসমীয়া বাক্য")
        bengali = IndicLIDDetector(bengali_model).predict("বাংলা বাক্য")

        self.assertEqual(assamese, {"lang": "assamese", "label": "asm_Beng", "score": 0.96})
        self.assertEqual(bengali, {"lang": "bengali", "label": "ben_Beng", "score": 0.98})
        self.assertEqual(assamese_model.calls[0][1], 2)

    def test_maps_english_and_hindi_labels(self) -> None:
        self.assertEqual(
            IndicLIDDetector(FakeFastTextModel("eng_Latn", 0.97)).predict("Hello")["lang"],
            "english",
        )
        self.assertEqual(
            IndicLIDDetector(FakeFastTextModel("hin_Deva", 0.97)).predict("नमस्ते")["lang"],
            "hindi",
        )

    def test_clamps_fasttext_rounding_above_one(self) -> None:
        prediction = IndicLIDDetector(FakeFastTextModel("asm_Beng", 1.00005)).predict("অসমীয়া")

        self.assertEqual(prediction["score"], 1.0)


class AssameseLanguageValidatorTests(unittest.TestCase):
    def test_accepts_assamese_examples_including_names_numbers_and_technical_terms(self) -> None:
        examples = [
            "নমস্কাৰ, আপুনি কেনে আছে?",
            "অসমৰ ৰাজধানী কি?",
            "কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ অসমীয়াত বুজাই দিয়ক।",
            "আজি ২০২৬ চনৰ ২৯ অক্টোবৰ। ৫টা উদাহৰণ দিয়ক।",
            "ৰীনা, Python API ব্যৱহাৰ কৰি সমস্যাটো সমাধান কৰাত সহায় কৰিবনে?",
            "মোৰ নাম ৰাহুল। Streamlit-ত chatbot কেনেকৈ আৰম্ভ কৰোঁ?",
        ]
        validator = AssameseLanguageValidator(FakeDetector("assamese", 0.93))

        for text in examples:
            with self.subTest(text=text):
                decision = validator.validate(text)
                self.assertTrue(decision.accepted)
                self.assertEqual(decision.language, "assamese")

    def test_rejects_bengali_despite_shared_script(self) -> None:
        examples = [
            "নমস্কার, আপনি কেমন আছেন?",
            "বাংলাদেশের রাজধানী কী?",
            "কৃত্রিম বুদ্ধিমত্তা কী? সহজ বাংলায় বুঝিয়ে দিন।",
        ]
        detector = FakeDetector("bengali", 0.98)
        validator = AssameseLanguageValidator(detector)

        for text in examples:
            with self.subTest(text=text):
                self.assertFalse(validator.validate(text).accepted)
        self.assertEqual(detector.calls, examples)

    def test_rejects_english_hindi_romanized_and_mixed_text(self) -> None:
        examples = [
            ("Hello, how are you?", "english"),
            ("What is artificial intelligence?", "english"),
            ("आप कैसे हैं?", "hindi"),
            ("कृत्रिम बुद्धिमत्ता क्या है?", "hindi"),
            ("Moi axomiya bhaxa xikibo bisaru.", "english"),
            ("Hello, আপুনি কেনে আছে?", "english"),
        ]

        for text, language in examples:
            with self.subTest(text=text):
                validator = AssameseLanguageValidator(FakeDetector(language, 0.99))
                self.assertFalse(validator.validate(text).accepted)

    def test_rejects_short_ambiguous_empty_punctuation_and_numbers_without_prediction(self) -> None:
        detector = FakeDetector("assamese", 0.99)
        validator = AssameseLanguageValidator(detector)

        for text in ("", "   ", "?!।", "১২৩৪", "হয়"):
            with self.subTest(text=text):
                self.assertFalse(validator.validate(text).accepted)
        self.assertEqual(detector.calls, [])

    def test_rejects_assamese_prediction_below_confidence_threshold(self) -> None:
        validator = AssameseLanguageValidator(
            FakeDetector("assamese", MIN_LANGUAGE_CONFIDENCE - 0.01)
        )

        self.assertFalse(validator.validate("অসমীয়া বাক্য").accepted)

    def test_rejects_roman_script_even_if_classifier_predicts_assamese(self) -> None:
        detector = IndicLIDDetector(FakeFastTextModel("asm_Latn", 0.99))
        validator = AssameseLanguageValidator(detector)

        decision = validator.validate("Moi axomiya bhaxa xikibo bisaru.")

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.label, "asm_Latn")

    def test_rejects_english_markers_in_mixed_input_before_classifier(self) -> None:
        detector = FakeDetector("assamese", 0.99)
        validator = AssameseLanguageValidator(detector)

        decision = validator.validate("Hello, আপুনি কেনে আছে?")

        self.assertFalse(decision.accepted)
        self.assertEqual(decision.reason, "mixed_language_marker")
        self.assertEqual(detector.calls, [])

    def test_allows_technical_terms_code_urls_and_names(self) -> None:
        examples = [
            "ৰীনা, Python API ব্যৱহাৰ কৰি সমস্যাটো সমাধান কৰাত সহায় কৰিবনে?",
            "মোৰ নাম ৰাহুল। Streamlit-ত chatbot কেনেকৈ আৰম্ভ কৰোঁ?",
            "এই URL টো চাওক: https://example.com/help",
            "এই code চলাওক: `print('hello world')` আৰু ফলাফল জনাওক।",
        ]
        validator = AssameseLanguageValidator(FakeDetector("assamese", 0.93))

        for text in examples:
            with self.subTest(text=text):
                self.assertTrue(validator.validate(text).accepted)


if __name__ == "__main__":
    unittest.main()
