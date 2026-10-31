"""国际化 (i18n) 翻译器

默认英文（en_US）；语言选择持久化到 <root>/config/language.json。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Optional

DEFAULT_LANG = "zh_CN"
SUPPORTED = {"en_US": "English", "zh_CN": "简体中文"}


class Translator:
    def __init__(self) -> None:
        self._languages: Dict[str, dict] = {}
        self._current_lang: str = DEFAULT_LANG
        self._load_all_languages()
        self._restore_choice()

    # ------------------------------------------------------------------
    def _locale_dir(self) -> Path:
        return Path(__file__).parent / "locales"

    def _load_all_languages(self) -> None:
        for lang_file in self._locale_dir().glob("*.json"):
            try:
                self._languages[lang_file.stem] = json.loads(
                    lang_file.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError):
                continue

    def _choice_file(self) -> Path:
        from vein_launcher.common.utils.path_utils import get_config_dir

        return get_config_dir() / "language.json"

    def _restore_choice(self) -> None:
        try:
            data = json.loads(self._choice_file().read_text(encoding="utf-8"))
            lang = data.get("lang")
            if lang in self._languages:
                self._current_lang = lang
        except (OSError, json.JSONDecodeError):
            pass

    def save_choice(self) -> None:
        try:
            path = self._choice_file()
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps({"lang": self._current_lang}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass

    # ------------------------------------------------------------------
    @property
    def current_lang(self) -> str:
        return self._current_lang

    @property
    def languages(self) -> Dict[str, str]:
        return {code: SUPPORTED.get(code, code) for code in self._languages}

    def set_language(self, lang_code: str) -> bool:
        if lang_code in self._languages:
            self._current_lang = lang_code
            return True
        return False

    def get(self, key: str, default: Optional[str] = None) -> str:
        langs = self._languages.get(self._current_lang, {})
        result = langs
        for part in key.split("."):
            if isinstance(result, dict) and part in result:
                result = result[part]
            else:
                return default if default is not None else key
        return str(result) if result is not None else key

    def t(self, key: str, default: Optional[str] = None) -> str:
        return self.get(key, default)


translator = Translator()


def _(key: str, default: Optional[str] = None) -> str:
    return translator.get(key, default)
