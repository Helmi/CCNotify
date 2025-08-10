"""
TTS (Text-to-Speech) providers for CCNotify
"""

from .base import TTSProvider
from .factory import get_tts_provider

__all__ = ["TTSProvider", "get_tts_provider"]
