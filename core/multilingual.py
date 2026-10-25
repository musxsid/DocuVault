"""
DocuVault — Multi-Language Document Detection & Cross-Lingual Engine
Detects document languages across Latin, Devanagari (Hindi), Cyrillic, and CJK scripts,
enabling unified English semantic queries over multi-lingual documents.
"""

import re
from typing import Dict, List, Optional, Tuple


class MultilingualEngine:
    """
    Language detection and multi-lingual query normalization engine.
    """

    LANGUAGE_PROFILES = {
        "Spanish": {
            "stopwords": {"el", "la", "de", "que", "y", "en", "un", "ser", "se", "no", "haber", "por", "con", "su", "para", "como", "estar", "tener", "le", "lo"},
            "script": "latin",
        },
        "French": {
            "stopwords": {"le", "la", "de", "un", "une", "et", "est", "il", "que", "ne", "en", "les", "des", "du", "par", "pour", "avec", "sur", "au"},
            "script": "latin",
        },
        "German": {
            "stopwords": {"der", "die", "das", "und", "in", "den", "von", "zu", "mit", "sich", "des", "auf", "f\u00fcr", "ist", "im", "dem", "nicht", "ein", "eine"},
            "script": "latin",
        },
        "Hindi": {
            "stopwords": {"\u0915\u0947", "\u0915\u0940", "\u0915\u093e", "\u092e\u0947\u0902", "\u0914\u0930", "\u0938\u0947", "\u0939\u0948", "\u0915\u094b", "\u092a\u0930", "\u0925\u093e", "\u0932\u093f\u090f", "\u092f\u0939", "\u0935\u0939"},
            "script": "devanagari",
        },
        "English": {
            "stopwords": {"the", "be", "to", "of", "and", "a", "in", "that", "have", "i", "it", "for", "not", "on", "with", "he", "as", "you", "do", "at"},
            "script": "latin",
        },
    }

    @classmethod
    def detect_language(cls, text: str) -> Dict[str, Any]:
        """
        Determines the primary language of the text.
        Returns detected language name, confidence score, and script type.
        """
        if not text or len(text.strip()) < 10:
            return {"language": "English", "confidence": 1.0, "script": "Latin"}

        # Script detection via Unicode blocks
        devanagari_chars = len(re.findall(r"[\u0900-\u097F]", text))
        cjk_chars = len(re.findall(r"[\u4E00-\u9FFF]", text))
        cyrillic_chars = len(re.findall(r"[\u0400-\u04FF]", text))
        total_len = len(text)

        if devanagari_chars / total_len > 0.15:
            return {"language": "Hindi", "confidence": 0.95, "script": "Devanagari"}
        if cjk_chars / total_len > 0.15:
            return {"language": "Chinese/CJK", "confidence": 0.95, "script": "CJK"}
        if cyrillic_chars / total_len > 0.15:
            return {"language": "Russian/Cyrillic", "confidence": 0.95, "script": "Cyrillic"}

        # Token stopword matching for Latin languages
        words = set(re.findall(r"\b[a-zA-Z\u00C0-\u017F]+\b", text.lower()))
        scores: Dict[str, int] = {}
        for lang, profile in cls.LANGUAGE_PROFILES.items():
            if profile["script"] == "latin":
                overlap = len(words & profile["stopwords"])
                scores[lang] = overlap

        best_lang = max(scores, key=scores.get) if scores and max(scores.values()) > 1 else "English"
        best_count = scores.get(best_lang, 1)
        conf = min(0.98, max(0.60, best_count / 15.0))

        return {
            "language": best_lang,
            "confidence": round(conf, 2),
            "script": "Latin",
        }
