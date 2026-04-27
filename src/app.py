"""LoL Chat Off — System tray application.

Provides a minimal Windows system tray interface to toggle League of Legends
chat visibility by managing firewall rules.
"""

from __future__ import annotations

import ctypes
import logging
import math
import sys
from collections.abc import Callable
from typing import Any

import pystray
from PIL import Image, ImageDraw

from firewall import FirewallError, FirewallManager
from i18n import Strings, get_strings
from servers import Region, detect_region

__all__ = ["main"]

logger = logging.getLogger(__name__)

_ICON_SIZE = 256

# Hextech color palette
_GOLD = (200, 170, 80)
_GOLD_DARK = (120, 90, 40)
_BG_ACTIVE = (5, 30, 50)
_BG_BLOCKED = (15, 25, 35)
_CYAN = (11, 196, 226)
_GRAY = (120, 120, 130)


def _draw_hexagon(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: float,
    **kwargs: Any,
) -> None:
    """Draw a regular hexagon centered at (cx, cy)."""
    points = [
        (
            cx + radius * math.cos(math.radians(60 * i - 90)),
            cy + radius * math.sin(math.radians(60 * i - 90)),
        )
        for i in range(6)
    ]
    draw.polygon(points, **kwargs)


def _is_admin() -> bool:
    """Check if the current process has administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except OSError:
        return False


def _elevate() -> None:
    """Relaunch the current process with UAC elevation and exit."""
    ctypes.windll.shell32.ShellExecuteW(
        None, "runas", sys.executable, " ".join(sys.argv), None, 1
    )
    raise SystemExit(0)


# pystray callback signature requires (icon, item) even when unused.
_TrayCallback = Callable[["pystray.Icon", "pystray.MenuItem"], None]


class TrayApp:
    """System tray application for toggling LoL chat blocking.

    Attributes:
        region: The currently selected server region.
    """

    def __init__(self, region: Region | None = None) -> None:
        self.region = region or detect_region()
        self._firewall = FirewallManager()
        self._strings: Strings = get_strings()
        self._icon: pystray.Icon | None = None  # type: ignore[assignment]

    def run(self) -> None:
        """Start the system tray icon and enter the event loop."""
        icon = pystray.Icon(
            name="LoLChatOff",
            icon=self._render_icon(),
            title=self._status_text,
            menu=self._build_menu(),
        )
        self._icon = icon  # type: ignore[assignment]
        logger.info("Starting tray application")
        icon.run()

    # ------------------------------------------------------------------
    # Icon rendering
    # ------------------------------------------------------------------

    def _render_icon(self) -> Image.Image:
        """Render a hextech-styled tray icon reflecting current state.

        - Active: cyan accent, dark blue background.
        - Blocked: gray accent, darker background, red X overlay.
        """
        blocked = self._firewall.is_blocked
        size = _ICON_SIZE
        img: Image.Image = Image.new("RGBA", (size, size))
        draw = ImageDraw.Draw(img)

        accent = _GRAY if blocked else _CYAN
        bg = _BG_BLOCKED if blocked else _BG_ACTIVE

        # Outer gold hexagon border
        _draw_hexagon(draw, size // 2, size // 2, 120, fill=_GOLD, outline=_GOLD_DARK)
        # Inner background
        _draw_hexagon(draw, size // 2, size // 2, 108, fill=bg)
        # Accent ring
        _draw_hexagon(draw, size // 2, size // 2, 90, outline=accent, width=2)

        # Chat bubble
        bx, by = size // 2, size // 2 - 10
        draw.rounded_rectangle([bx - 45, by - 28, bx + 45, by + 22], radius=6, fill=accent)
        draw.polygon([(bx - 20, by + 22), (bx - 8, by + 22), (bx - 30, by + 46)], fill=accent)

        # Inner bubble inset
        inner = tuple(max(0, c - 60) for c in accent)
        draw.rounded_rectangle([bx - 38, by - 21, bx + 38, by + 15], radius=4, fill=inner)

        # Text lines inside bubble
        line_color = (255, 255, 255, 180)
        draw.rounded_rectangle([bx - 30, by - 14, bx + 20, by - 6], radius=2, fill=line_color)
        draw.rounded_rectangle([bx - 30, by - 2, bx + 10, by + 6], radius=2, fill=line_color)

        # Red X when blocked
        if blocked:
            draw.line([(bx - 35, by - 30), (bx + 35, by + 40)], fill=(200, 30, 30), width=6)
            draw.line([(bx + 35, by - 30), (bx - 35, by + 40)], fill=(200, 30, 30), width=6)
            draw.line([(bx - 35, by - 30), (bx + 35, by + 40)], fill=(255, 80, 80), width=4)
            draw.line([(bx + 35, by - 30), (bx - 35, by + 40)], fill=(255, 80, 80), width=4)

        # Corner energy dots
        for angle_deg in (30, 150, 270):
            angle = math.radians(angle_deg)
            dx = size // 2 + 100 * math.cos(angle)
            dy = size // 2 + 100 * math.sin(angle)
            draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=_GOLD)

        return img

    # ------------------------------------------------------------------
    # Menu construction
    # ------------------------------------------------------------------

    @property
    def _status_text(self) -> str:
        s = self._strings
        template = s.status_blocked if self._firewall.is_blocked else s.status_active
        return template.format(region=self.region.name)

    def _build_menu(self) -> pystray.Menu:
        s = self._strings
        blocked = self._firewall.is_blocked
        toggle_label = s.enable_chat if blocked else s.disable_chat

        region_items = tuple(
            pystray.MenuItem(
                region.name,
                self._region_handler(region),
                checked=lambda item, r=region: self.region is r,
            )
            for region in Region
        )

        return pystray.Menu(
            pystray.MenuItem(self._status_text, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(toggle_label, self._on_toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(s.region, pystray.Menu(*region_items)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(s.quit, self._on_quit),
        )

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_toggle(self, _icon: object, _item: object) -> None:
        try:
            if self._firewall.is_blocked:
                self._firewall.unblock()
            else:
                self._firewall.block(self.region.hostname)
        except FirewallError:
            logger.exception("Failed to toggle firewall rules")
        self._refresh()

    def _region_handler(self, region: Region) -> _TrayCallback:
        def handler(_icon: object, _item: object) -> None:
            self.region = region
            self._refresh()
        return handler  # type: ignore[return-value]

    @staticmethod
    def _on_quit(icon: object, _item: object) -> None:
        icon.stop()  # type: ignore[union-attr]

    # ------------------------------------------------------------------
    # State management
    # ------------------------------------------------------------------

    def _refresh(self) -> None:
        """Synchronize the tray icon and menu with current firewall state."""
        if self._icon is None:
            return
        self._icon.icon = self._render_icon()
        self._icon.title = self._status_text
        self._icon.menu = self._build_menu()


def main() -> None:
    """Application entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    if not _is_admin():
        logger.info("Not running as admin, requesting elevation")
        _elevate()

    app = TrayApp()
    app.run()


if __name__ == "__main__":
    main()
