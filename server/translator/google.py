"""
Google Translate 翻译适配器
"""
from .base import Translator, TranslationError


class GoogleTranslator(Translator):
    """Google Translate 翻译适配器"""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def translate(
        self,
        text: str,
        source_lang: str = None,
        target_lang: str = "zh"
    ) -> str:
        """使用 Google Translate 翻译"""
        if not self.api_key:
            raise TranslationError("Google API Key 未设置，请在 config.yaml 中配置")

        from google.cloud import translate_v2 as translate

        client = translate.Client()

        result = client.translate(
            text,
            target_language=target_lang,
            source_language=source_lang
        )

        return result["translatedText"]

    def get_supported_languages(self) -> list:
        """获取支持的语言"""
        return [
            "af", "ar", "bg", "bn", "ca", "cs", "cy", "da", "de", "el",
            "en", "eo", "es", "et", "fa", "fi", "fr", "gu", "he", "hi",
            "hr", "hu", "id", "is", "it", "ja", "kn", "ko", "lt", "lv",
            "mk", "ml", "mr", "ms", "nl", "pa", "pl", "pt", "ro", "ru",
            "sk", "sl", "sq", "sv", "sw", "ta", "te", "th", "tl", "tr",
            "uk", "ur", "vi", "zh"
        ]
