"""国际化 (i18n) 翻译器"""

import json
from pathlib import Path
from typing import Optional


class Translator:
    """多语言翻译器"""
    
    def __init__(self):
        self._languages: dict[str, dict] = {}
        self._current_lang: str = "zh_CN"
        self._load_all_languages()
    
    def _load_all_languages(self) -> None:
        """加载所有语言文件"""
        locale_dir = Path(__file__).parent / "locales"
        
        for lang_file in locale_dir.glob("*.json"):
            lang_code = lang_file.stem  # zh_CN, en_US
            try:
                data = json.loads(lang_file.read_text(encoding="utf-8"))
                self._languages[lang_code] = data
            except Exception as e:
                print(f"Failed to load {lang_file}: {e}")
    
    def set_language(self, lang_code: str) -> bool:
        """切换语言"""
        if lang_code in self._languages:
            self._current_lang = lang_code
            return True
        return False
    
    def get(self, key: str, default: Optional[str] = None) -> str:
        """
        获取翻译文本
        
        Args:
            key: 键名，支持点号分隔如 "nav.home"
            default: 如果找不到翻译时返回的默认值
            
        Returns:
            翻译后的文本
        """
        langs = self._languages.get(self._current_lang, {})
        
        # 按点号分割键名，逐层访问字典
        parts = key.split(".")
        result = langs
        
        try:
            for part in parts:
                if isinstance(result, dict):
                    result = result[part]
                else:
                    # 找不到时返回默认值或原始键
                    return default if default is not None else key
            
            return str(result) if result is not None else key
        except (KeyError, TypeError):
            return default if default is not None else key
    
    def t(self, key: str, default: Optional[str] = None) -> str:
        """翻译别名（方便使用）"""
        return self.get(key, default)


# 全局单例
translator = Translator()

def _(key: str, default: Optional[str] = None) -> str:
    """
    翻译快捷函数（类似 gettext 的 _() 语法）
    
    示例：
        label = _("nav.home")
    """
    return translator.get(key, default)
