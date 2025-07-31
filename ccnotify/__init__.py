"""
CCNotify - Intelligent notification system for Claude Code with audio feedback
"""

__version__ = "0.1.0"
__author__ = "Helmi"
__license__ = "MIT"

from .tts import TTSProvider, get_tts_provider

__all__ = ["TTSProvider", "get_tts_provider"]