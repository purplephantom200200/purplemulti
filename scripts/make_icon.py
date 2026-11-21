"""
Build assets/icon.ico and the README picture from the square artwork in assets/icon-source.png.

Small icons (taskbar, title bar) use a tight crop on the main window so they stay
readable; large ones (Start Menu, Explorer) show the stacked windows.

    uv run python scripts/make_icon.py [path/to/artwork.png]
"""

from __future__ import annotations

import struct
import sys
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice, QRect, Qt
from PySide6.QtGui import QGuiApplication, QImage

ASSETS = Path(__file__).resolve().parents[1] / "assets"
SOURCE = ASSETS / "icon-source.png"
ICON = ASSETS / "icon.ico"
BANNER = ASSETS / "purplemulti.png"

# Crops as fractions of the artwork (x, y, size), measured on the 1254 px original.
LARGE_CROP = (250 / 1254, 260 / 1254, 760 / 1254)
SMALL_CROP = (370 / 1254, 340 / 1254, 540 / 1254)
LARGE_SIZES = (256, 128, 64, 48)
SMALL_SIZES = (40, 32, 24, 20, 16)
BANNER_SIZE = 512


def crop(image: QImage, fractions: tuple[float, float, float]) -> QImage:
    side = min(image.width(), image.height())
    x, y, size = (round(value * side) for value in fractions)
    return image.copy(QRect(x, y, size, size))


def png_bytes(image: QImage, size: int) -> bytes:
    scaled = image.scaled(size, size, Qt.AspectRatioMode.IgnoreAspectRatio,
                          Qt.TransformationMode.SmoothTransformation)
    buffer = QBuffer()
    buffer.open(QIODevice.OpenModeFlag.WriteOnly)
    scaled.convertToFormat(QImage.Format.Format_ARGB32).save(buffer, "PNG")
    return bytes(buffer.data())


def write_ico(path: Path, images: list[tuple[int, bytes]]) -> None:
    """ICO with PNG-compressed entries, which Windows reads at every size."""
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = len(header) + 16 * len(images)
    directory = b""
    for size, data in images:
        directory += struct.pack("<BBBBHHII", size % 256, size % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    path.write_bytes(header + directory + b"".join(data for _, data in images))


def main(argv: list[str]) -> int:
    source = Path(argv[1]) if len(argv) > 1 else SOURCE
    app = QGuiApplication.instance() or QGuiApplication([])  # noqa: F841 - image plugins
    artwork = QImage(str(source))
    if artwork.isNull():
        print(f"[ERROR] Could not read {source}")
        return 1
    if source != SOURCE:
        artwork.save(str(SOURCE), "PNG")
    large, small = crop(artwork, LARGE_CROP), crop(artwork, SMALL_CROP)
    entries = [(size, png_bytes(large, size)) for size in LARGE_SIZES]
    entries += [(size, png_bytes(small, size)) for size in SMALL_SIZES]
    write_ico(ICON, entries)
    BANNER.write_bytes(png_bytes(artwork, BANNER_SIZE))
    print(f"[SUCCESS] Wrote {ICON} ({len(entries)} sizes) and {BANNER}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
