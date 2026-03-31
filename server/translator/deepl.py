"""
DeepL 翻译适配器
"""
from .base import Translator, TranslationError


class DeepLTranslator(Translator):
    """DeepL 翻译适配器"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.api_url = "https://api-free.deepl.com/v2/translate"

    def translate(
        self,
        text: str,
        source_lang: str = None,
        target_lang: str = "zh"
    ) -> str:
        """使用 DeepL 翻译"""
        if not self.api_key:
            raise TranslationError("DeepL API Key 未设置，请在 config.yaml 中配置")

        import requests

        params = {
            "auth_key": self.api_key,
            "text": text,
            "target_lang": target_lang.upper()
        }

        if source_lang:
            params["source_lang"] = source_lang.upper()

        try:
            response = requests.post(self.api_url, data=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            if result.get("translations"):
                return result["translations"][0]["text"]
            return text

        except requests.RequestException as e:
            raise TranslationError(f"DeepL 翻译失败: {e}")

    def get_supported_languages(self) -> list:
        """获取支持的语言"""
        return [
            "BG", "CS", "DA", "DE", "EL", "EN", "ES", "ET", "FI",
            "FR", "HU", "IT", "JA", "LT", "LV", "NL", "PL", "PT",
            "RO", "RU", "SK", "SL", "SV", "UK", "ZH"
        ]
