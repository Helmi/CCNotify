"""CCNotify installer package."""

from .detector import InstallationDetector, InstallationStatus
from .welcome import display_welcome_screen, display_success_message, display_error_message
from .flows import FirstTimeFlow, UpdateFlow

__all__ = [
    "InstallationDetector",
    "InstallationStatus",
    "display_welcome_screen",
    "display_success_message",
    "display_error_message",
    "FirstTimeFlow",
    "UpdateFlow",
]
