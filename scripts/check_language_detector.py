from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from language_validator import get_language_validator


SAMPLES = (
    ("assamese", "নমস্কাৰ, আপুনি কেনে আছে?"),
    ("assamese", "অসমৰ ৰাজধানী কি?"),
    ("assamese", "কৃত্ৰিম বুদ্ধিমত্তা কি? সহজ অসমীয়াত বুজাই দিয়ক।"),
    ("assamese", "আজি ২০২৬ চনৰ ২৯ অক্টোবৰ। ৫টা উদাহৰণ দিয়ক।"),
    ("assamese", "ৰীনা, Python API ব্যৱহাৰ কৰি সমস্যাটো সমাধান কৰাত সহায় কৰিবনে?"),
    ("assamese", "মোৰ নাম ৰাহুল। Streamlit-ত chatbot কেনেকৈ আৰম্ভ কৰোঁ?"),
    ("bengali", "নমস্কার, আপনি কেমন আছেন?"),
    ("bengali", "বাংলাদেশের রাজধানী কী?"),
    ("bengali", "কৃত্রিম বুদ্ধিমত্তা কী? সহজ বাংলায় বুঝিয়ে দিন।"),
    ("bengali", "আমি আজ স্কুলে যাব।"),
    ("english", "Hello, how are you?"),
    ("english", "What is artificial intelligence?"),
    ("hindi", "आप कैसे हैं?"),
    ("hindi", "कृत्रिम बुद्धिमत्ता क्या है?"),
    ("other", "Moi axomiya bhaxa xikibo bisaru."),
    ("other", "Hello, আপুনি কেনে আছে?"),
)


def main() -> int:
    validator = get_language_validator()
    errors = 0
    for expected, text in SAMPLES:
        decision = validator.validate(text)
        actual = decision.language if decision.confidence is not None else "short/ambiguous"
        passed = decision.accepted if expected == "assamese" else not decision.accepted
        if not passed:
            errors += 1
        print(
            f"EXPECTED={expected} PREDICTED={actual} LABEL={decision.label} "
            f"SCORE={decision.confidence} ACCEPT={decision.accepted} PASS={passed} "
            f"TEXT={text.encode('unicode_escape').decode('ascii')}"
        )

    print(f"RESULTS={len(SAMPLES) - errors}/{len(SAMPLES)} EXPECTED_GATE_DECISIONS_MATCHED")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
