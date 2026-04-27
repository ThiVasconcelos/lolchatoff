"""Riot Games chat server registry.

Maps region identifiers to their corresponding chat server hostnames.
These endpoints are used by the League of Legends client for XMPP-based
chat communication.
"""

from __future__ import annotations

import ctypes
import logging
from enum import Enum

__all__ = ["Region", "detect_region"]

logger = logging.getLogger(__name__)

# Maps locale language_country codes to the most likely LoL region.
_LOCALE_TO_REGION: dict[str, str] = {
    "pt_BR": "BR",
    "en_US": "NA",
    "en_AU": "OCE",
    "en_NZ": "OCE",
    "en_GB": "EUW",
    "fr_FR": "EUW",
    "de_DE": "EUW",
    "it_IT": "EUW",
    "es_ES": "EUW",
    "pt_PT": "EUW",
    "nl_NL": "EUW",
    "pl_PL": "EUNE",
    "cs_CZ": "EUNE",
    "el_GR": "EUNE",
    "hu_HU": "EUNE",
    "ro_RO": "EUNE",
    "es_MX": "LAN",
    "es_AR": "LAS",
    "es_CL": "LAS",
    "es_CO": "LAN",
    "es_PE": "LAS",
    "ja_JP": "JP",
    "ru_RU": "RU",
    "tr_TR": "TR",
    "th_TH": "TH",
    "vi_VN": "VN",
    "zh_TW": "TW",
    "tl_PH": "PH",
}


class Region(Enum):
    """Supported Riot Games chat regions with their server hostnames."""

    BR = "br.chat.si.riotgames.com"
    NA = "na2.chat.si.riotgames.com"
    EUW = "euw1.chat.si.riotgames.com"
    EUNE = "eun1.chat.si.riotgames.com"
    LAN = "la1.chat.si.riotgames.com"
    LAS = "la2.chat.si.riotgames.com"
    JP = "jp1.chat.si.riotgames.com"
    OCE = "oc1.chat.si.riotgames.com"
    RU = "ru1.chat.si.riotgames.com"
    TR = "tr1.chat.si.riotgames.com"
    PH = "ph1.chat.si.riotgames.com"
    SG = "sg1.chat.si.riotgames.com"
    TH = "th1.chat.si.riotgames.com"
    TW = "tw1.chat.si.riotgames.com"
    VN = "vn1.chat.si.riotgames.com"

    @property
    def hostname(self) -> str:
        """The fully qualified chat server hostname."""
        return self.value


# Windows LANGID -> locale code (primary mappings)
_LANGID_TO_LOCALE: dict[int, str] = {
    0x0416: "pt_BR",  # Portuguese (Brazil)
    0x0816: "pt_PT",  # Portuguese (Portugal)
    0x0409: "en_US",  # English (US)
    0x0809: "en_GB",  # English (UK)
    0x0C09: "en_AU",  # English (Australia)
    0x1409: "en_NZ",  # English (New Zealand)
    0x040C: "fr_FR",  # French
    0x0407: "de_DE",  # German
    0x0410: "it_IT",  # Italian
    0x0C0A: "es_ES",  # Spanish (Spain)
    0x080A: "es_MX",  # Spanish (Mexico)
    0x2C0A: "es_AR",  # Spanish (Argentina)
    0x340A: "es_CL",  # Spanish (Chile)
    0x240A: "es_CO",  # Spanish (Colombia)
    0x280A: "es_PE",  # Spanish (Peru)
    0x0411: "ja_JP",  # Japanese
    0x0419: "ru_RU",  # Russian
    0x041F: "tr_TR",  # Turkish
    0x041E: "th_TH",  # Thai
    0x042A: "vi_VN",  # Vietnamese
    0x0404: "zh_TW",  # Chinese (Taiwan)
    0x0415: "pl_PL",  # Polish
    0x0405: "cs_CZ",  # Czech
    0x0408: "el_GR",  # Greek
    0x040E: "hu_HU",  # Hungarian
    0x0418: "ro_RO",  # Romanian
    0x0413: "nl_NL",  # Dutch
    0x0464: "tl_PH",  # Filipino
}


def detect_region() -> Region:
    """Detect the most likely LoL region based on the Windows UI language.

    Uses the Win32 ``GetUserDefaultUILanguage`` API to read the OS
    language and maps it to a LoL server region.
    Falls back to ``Region.NA`` when detection fails.
    """
    try:
        lang_id: int = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        logger.debug("Could not read Windows UI language, defaulting to NA")
        return Region.NA

    locale_code = _LANGID_TO_LOCALE.get(lang_id)
    if locale_code is None:
        logger.debug("No mapping for LANGID 0x%04X, defaulting to NA", lang_id)
        return Region.NA

    region_name = _LOCALE_TO_REGION.get(locale_code)
    if region_name is None:
        logger.debug("No region for locale %r, defaulting to NA", locale_code)
        return Region.NA

    logger.info("Detected LANGID 0x%04X -> %s -> %s", lang_id, locale_code, region_name)
    return Region[region_name]
