"""
翻译模块 - 抽象基类
"""
from abc import ABC, abstractmethod
from typing import Optional


class Translator(ABC):
    """翻译器抽象基类"""

    @abstractmethod
    def translate(
        self,
        text: str,
        source_lang: Optional[str] = None,
        target_lang: str = "zh"
    ) -> str:
        """翻译文本

        Args:
            text: 待翻译文本
            source_lang: 源语言 (None 表示自动检测)
            target_lang: 目标语言

        Returns:
            翻译后的文本
        """
        pass

    @abstractmethod
    def get_supported_languages(self) -> list:
        """获取支持的语言列表"""
        pass


class TranslationError(Exception):
    """翻译错误异常"""
    pass
