"""
OpenAI 翻译适配器
"""
from .base import Translator, TranslationError


class OpenAITranslator(Translator):
    """OpenAI (GPT) 翻译适配器"""

    def __init__(self, api_key: str = "", model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model

    def translate(
        self,
        text: str,
        source_lang: str = None,
        target_lang: str = "zh"
    ) -> str:
        """使用 OpenAI GPT 翻译"""
        if not self.api_key:
            raise TranslationError("OpenAI API Key 未设置，请在 config.yaml 中配置")

        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        # 构建提示词
        if source_lang:
            prompt = f"Translate the following {source_lang} text to {target_lang}: {text}"
        else:
            prompt = f"Detect the language and translate to {target_lang}: {text}"

        try:
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a professional translator."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )

            return response.choices[0].message.content

        except Exception as e:
            raise TranslationError(f"OpenAI 翻译失败: {e}")

    def get_supported_languages(self) -> list:
        """获取支持的语言（GPT 支持所有语言）"""
        return [
            "af", "ar", "bg", "bn", "ca", "cs", "cy", "da", "de", "el",
            "en", "eo", "es", "et", "fa", "fi", "fr", "gu", "he", "hi",
            "hr", "hu", "id", "is", "it", "ja", "kn", "ko", "lt", "lv",
            "mk", "ml", "mr", "ms", "nl", "pa", "pl", "pt", "ro", "ru",
            "sk", "sl", "sq", "sv", "sw", "ta", "te", "th", "tl", "tr",
            "uk", "ur", "vi", "zh"
        ]
