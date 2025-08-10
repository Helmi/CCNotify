"""
CCNotify - Intelligent notification system for Claude Code with audio feedback
"""

__version__ = "0.1.13"
__author__ = "Helmi"
__license__ = "MIT"


# Lazy imports to avoid heavy dependencies during CLI usage
def get_tts_provider(*args, **kwargs):
    """Lazy import wrapper for TTS provider"""
    from .tts import get_tts_provider as _get_tts_provider

    return _get_tts_provider(*args, **kwargs)


def get_tts_provider_class():
    """Lazy import wrapper for TTS provider class"""
    from .tts import TTSProvider

    return TTSProvider


__all__ = ["get_tts_provider", "get_tts_provider_class"]
