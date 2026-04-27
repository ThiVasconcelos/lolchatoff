"""Build script to create a portable .exe with PyInstaller."""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw

_ROOT = Path(__file__).parent
_SRC = _ROOT / "src"
_ASSETS = _ROOT / "assets"
_ICON = _ASSETS / "icon.ico"
_ENTRY = _SRC / "app.py"

# Hextech palette (matches src/app.py)
_GOLD = (200, 170, 80)
_GOLD_DARK = (120, 90, 40)
_BG = (5, 30, 50)
_CYAN = (11, 196, 226)


def _draw_hexagon(
    draw: ImageDraw.ImageDraw,
    cx: float,
    cy: float,
    radius: float,
    **kwargs: Any,
) -> None:
    points = [
        (
            cx + radius * math.cos(math.radians(60 * i - 90)),
            cy + radius * math.sin(math.radians(60 * i - 90)),
        )
        for i in range(6)
    ]
    draw.polygon(points, **kwargs)


def generate_icon() -> None:
    """Generate a hextech-styled .ico file for the executable."""
    size = 256
    img = Image.new("RGBA", (size, size))
    draw = ImageDraw.Draw(img)

    _draw_hexagon(draw, size // 2, size // 2, 120, fill=_GOLD, outline=_GOLD_DARK)
    _draw_hexagon(draw, size // 2, size // 2, 108, fill=_BG)
    _draw_hexagon(draw, size // 2, size // 2, 90, outline=_CYAN, width=2)

    bx, by = size // 2, size // 2 - 10
    draw.rounded_rectangle([bx - 45, by - 28, bx + 45, by + 22], radius=6, fill=_CYAN)
    draw.polygon([(bx - 20, by + 22), (bx - 8, by + 22), (bx - 30, by + 46)], fill=_CYAN)

    inner = tuple(max(0, c - 60) for c in _CYAN)
    draw.rounded_rectangle([bx - 38, by - 21, bx + 38, by + 15], radius=4, fill=inner)

    line_color = (255, 255, 255, 180)
    draw.rounded_rectangle([bx - 30, by - 14, bx + 20, by - 6], radius=2, fill=line_color)
    draw.rounded_rectangle([bx - 30, by - 2, bx + 10, by + 6], radius=2, fill=line_color)

    for angle_deg in (30, 150, 270):
        angle = math.radians(angle_deg)
        dx = size // 2 + 100 * math.cos(angle)
        dy = size // 2 + 100 * math.sin(angle)
        draw.ellipse([dx - 4, dy - 4, dx + 4, dy + 4], fill=_GOLD)

    _ASSETS.mkdir(exist_ok=True)
    img.save(str(_ICON), format="ICO", sizes=[(256, 256), (48, 48), (32, 32), (16, 16)])
    print(f"Icon generated: {_ICON}")


def main() -> None:
    """Generate the icon and run PyInstaller."""
    generate_icon()

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--noconsole",
        "--name", "LoLChatOff",
        "--icon", str(_ICON),
        "--paths", str(_SRC),
        str(_ENTRY),
    ]
    subprocess.run(cmd, check=True)
    print("\nBuild complete! Output: dist/LoLChatOff.exe")


if __name__ == "__main__":
    main()
