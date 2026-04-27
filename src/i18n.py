"""Internationalization support for LoL Chat Off.

Provides translated UI strings based on the Windows system language.
Currently supports English (default) and Brazilian Portuguese.
"""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass

__all__ = ["Strings", "get_strings"]

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Strings:
    """All user-facing strings for the tray menu."""

    status_active: str
    status_blocked: str
    enable_chat: str
    disable_chat: str
    region: str
    quit: str


_EN = Strings(
    status_active="LoL Chat: ACTIVE [{region}]",
    status_blocked="LoL Chat: BLOCKED [{region}]",
    enable_chat="Enable Chat",
    disable_chat="Disable Chat",
    region="Region",
    quit="Quit",
)

_PT = Strings(
    status_active="LoL Chat: ATIVO [{region}]",
    status_blocked="LoL Chat: BLOQUEADO [{region}]",
    enable_chat="Ativar Chat",
    disable_chat="Desativar Chat",
    region="Região",
    quit="Sair",
)

# Primary language ID (lower byte of LANGID) -> Strings
_LANG_MAP: dict[int, Strings] = {
    0x16: _PT,  # Portuguese
}


def get_strings() -> Strings:
    """Return the appropriate UI strings based on the Windows UI language.

    Falls back to English when the language cannot be detected or
    has no translation available.
    """
    try:
        lang_id: int = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        logger.debug("Could not read Windows UI language, defaulting to English")
        return _EN

    primary_lang = lang_id & 0xFF
    strings = _LANG_MAP.get(primary_lang, _EN)

    logger.info(
        "Detected LANGID 0x%04X (primary=0x%02X) -> %s",
        lang_id,
        primary_lang,
        "pt" if strings is _PT else "en",
    )
    return strings
