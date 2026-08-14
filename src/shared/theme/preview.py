"""Preview rendering helpers for themes."""
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt

from shared.theme.core import _PREVIEW_COLOURS


def theme_preview_pixmap(name: str, size: int = 20):
    bg, accent, text = _PREVIEW_COLOURS.get(name, ("#808080", "#404040", "#ffffff"))
    pm = QPixmap(size, size)
    pm.fill(QColor(bg))
    painter = QPainter(pm)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(QColor(accent))
    painter.drawRoundedRect(0, 0, size // 3, size, 3, 3)
    painter.setBrush(QColor(text))
    cx, cy = size // 6, size // 2
    painter.drawEllipse(cx - 2, cy - 2, 4, 4)
    painter.end()
    from PyQt6.QtGui import QIcon

    return QIcon(pm)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
