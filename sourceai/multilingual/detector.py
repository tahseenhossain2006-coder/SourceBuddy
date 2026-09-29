# sourceai/multilingual/detector.py
from typing import Optional
def detect_language(text: str) -> str:
    try:
        from langdetect import detect
        return detect(text)
    except Exception:
        return "en"