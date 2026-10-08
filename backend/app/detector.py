from langdetect import DetectorFactory, detect_langs
from langdetect.lang_detect_exception import LangDetectException

# langdetect is random by default; a fixed seed makes it give the same answer every run.
DetectorFactory.seed = 0


def detect_language(text: str) -> tuple[str, float]:
    """Return (language_code, confidence) for the text."""
    try:
        best = detect_langs(text)[0]
    except LangDetectException:
        return "unknown", 0.0
    # langdetect says "zh-cn" for Chinese; keep just "zh" to match our language list.
    return best.lang.split("-")[0], round(best.prob, 3)