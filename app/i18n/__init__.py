"""
Internationalisation — Production Grade
Runtime dynamic language loading.
UI MUST use t() to get display strings.
Services return semantic keys, not display strings.

Supported languages Phase 1:
  en — English
  es — Spanish
  fr — French
  de — German
"""

import json
import os
from typing import Dict

_SUPPORTED_LANGUAGES = {"en", "es", "fr", "de"}
_DEFAULT_LANGUAGE = "en"
_I18N_DIR = os.path.dirname(__file__)

# Cache loaded dictionaries to avoid repeated disk reads
_cache: Dict[str, Dict[str, str]] = {}


def load_language(lang_code: str) -> Dict[str, str]:
    """
    Loads and returns the translation dictionary for the given language code.
    Falls back to English if the language is unsupported or file missing.

    Args:
        lang_code: ISO 639-1 language code ('en', 'es', 'fr', 'de')

    Returns:
        Dictionary of key → translated string
    """
    if lang_code not in _SUPPORTED_LANGUAGES:
        lang_code = _DEFAULT_LANGUAGE

    if lang_code in _cache:
        return _cache[lang_code]

    file_path = os.path.join(_I18N_DIR, f"{lang_code}.json")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            translations = json.load(f)
        _cache[lang_code] = translations
        return translations
    except FileNotFoundError:
        # Fallback to English
        if lang_code != _DEFAULT_LANGUAGE:
            return load_language(_DEFAULT_LANGUAGE)
        return {}


def t(key: str, lang_code: str = "en", **kwargs) -> str:
    """
    Translate a semantic key to the display string for the given language.
    Supports simple placeholder substitution via kwargs.

    Args:
        key:       Semantic key (e.g. 'btn_save', 'msg_saved')
        lang_code: Language code for translation
        **kwargs:  Optional format parameters (e.g. min=2)

    Returns:
        Translated and formatted string. Falls back to key if not found.

    Example:
        t("err_min_length", "es", min=3)
        # → "Debe tener al menos 3 caracteres."
    """
    translations = load_language(lang_code)
    text = translations.get(key)

    if text is None:
        # Fallback to English
        fallback = load_language(_DEFAULT_LANGUAGE)
        text = fallback.get(key, key)

    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError):
            pass

    return text


def get_supported_languages() -> Dict[str, str]:
    """
    Returns a dict mapping lang_code → native name for UI language selector.
    """
    return {
        "en": "English",
        "es": "Español",
        "fr": "Français",
        "de": "Deutsch",
    }


def is_supported(lang_code: str) -> bool:
    """Returns True if lang_code is a supported language."""
    return lang_code in _SUPPORTED_LANGUAGES
