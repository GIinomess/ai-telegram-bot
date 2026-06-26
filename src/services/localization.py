from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from src.config.constants import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES


class LocalizationService:
    def __init__(self) -> None:
        self._translations: dict[str, dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        locales_dir = Path(__file__).parent.parent / "locales"
        for lang in SUPPORTED_LANGUAGES:
            path = locales_dir / f"{lang}.json"
            if path.exists():
                with open(path, encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self._translations[lang] = cast(dict[str, str], data)

    def get(self, key: str, locale: str, **kwargs: object) -> str:
        text = self._translations.get(locale, {}).get(key)
        if text is None:
            text = self._translations.get(DEFAULT_LANGUAGE, {}).get(key)
        if text is None:
            text = key
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, IndexError):
                pass
        return text

    def get_supported_languages(self) -> list[str]:
        return list(SUPPORTED_LANGUAGES)
