"""
翻译模块 - 统一工厂函数
支持多种翻译服务提供商
"""
from .base import Translator, TranslationError
from .deepl import DeepLTranslator
from .google import GoogleTranslator
from .openai import OpenAITranslator

# 提供商映射
TRANSLATORS = {
    "deepl": DeepLTranslator,
    "google": GoogleTranslator,
    "openai": OpenAITranslator,
}


def create_translator(provider: str, api_key: str = "", **kwargs) -> Translator:
    """创建翻译器实例

    Args:
        provider: 提供商名称 ("deepl", "google", "openai")
        api_key: API 密钥
        **kwargs: 其他参数

    Returns:
        Translator 实例
    """
    if provider not in TRANSLATORS:
        raise ValueError(f"不支持的翻译提供商: {provider}，支持: {list(TRANSLATORS.keys())}")

    translator_class = TRANSLATORS[provider]
    return translator_class(api_key=api_key, **kwargs)


def get_available_providers() -> list:
    """获取可用的提供商列表"""
    return list(TRANSLATORS.keys())
