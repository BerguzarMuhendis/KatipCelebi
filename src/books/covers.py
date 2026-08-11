# Katip Celebi
# Copyright (C) 2026 farukylmz0550
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""Fetching cover pictures without making the user wait for them.

Everything drawn here -- the cropped covers and the placeholder panels -- is
made at the screen's real pixel density, not at the logical size the layout
asks for. On a 150%-scaled display a "150x210" panel is really 225x315
physical pixels; drawing it at 150x210 and letting Qt stretch it is how a
cover comes out soft next to crisp text. See `_device_ratio`.
"""

import logging

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtGui import QImage, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import QApplication

from books import openlibrary
from books.openlibrary import COVER_SIZE_THUMB
from shared.theme import colour

logger = logging.getLogger("katipcelebi")

THUMB_SIZE = (150, 210)
LARGE_SIZE = (260, 380)

# Enough to fill a screen of covers quickly, few enough that they can never
# crowd out anything else. Covers are the app's idea, not the user's: an ISBN
# lookup they actually asked for must never queue behind a hundred of them.
COVER_THREADS = 4


class CoverSignals(QObject):
    """One hub for every cover task, so the pictures can reach the window."""

    loaded = pyqtSignal(str, str, QImage)  # key, size, image
    failed = pyqtSignal(str, str)  # key, size


class CoverTask(QRunnable):
    """Fetch one cover, in the background."""

    def __init__(self, key: str, size: str, signals: CoverSignals):
        super().__init__()
        self.key = key
        self.size = size
        self.signals = signals

    def run(self):
        # Nothing may escape from here. PyQt turns an unhandled exception
        # inside a Qt thread into qFatal(), which ends the process on the spot:
        # no dialog, no log line, no chance to save. A missing cover is not
        # worth the user's library.
        try:
            # Through the module, not a bound name: a test that swaps
            # openlibrary.fetch_cover for a fake needs this call to see it, or
            # every test quietly hits the real network.
            data = openlibrary.fetch_cover(self.key, self.size)
            if data:
                image = QImage.fromData(data)
                if not image.isNull():
                    self.signals.loaded.emit(self.key, self.size, image)
                    return
        except Exception:
            logger.exception("Cover fetch failed for %s", self.key)
        self.signals.failed.emit(self.key, self.size)


class CoverLoader:
    """Asks for covers, on threads of its own, and remembers the answers.

    A cover, once fetched, is kept in memory. The grid throws its cards away
    and builds fresh ones on every refresh -- adding a book, changing the
    theme, changing the language -- and the book page is opened anew each time.
    Without a memory the second request for a cover was deduplicated against
    the first and simply never answered, so every cover vanished after the
    first refresh and never came back. Now the second request is answered from
    the cache, on the spot.
    """

    def __init__(self):
        self.signals = CoverSignals()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(COVER_THREADS)
        self._asked: set[tuple[str, str]] = set()
        self._images: dict[tuple[str, str], QImage] = {}
        self.signals.loaded.connect(self._remember)

    def _remember(self, key: str, size: str, image: QImage) -> None:
        self._images[(key, size)] = image

    def request(self, key: str, size: str = COVER_SIZE_THUMB) -> None:
        """Get a cover to whoever is listening.

        From memory and at once if it has been fetched before; off a thread if
        it has not. A generated key is not an ISBN, so there is nothing to ask
        about.
        """
        from books.model import LOCAL_KEY_PREFIX

        if not key or key.startswith(LOCAL_KEY_PREFIX):
            return
        cached = self._images.get((key, size))
        if cached is not None:
            # Straight back to the caller, synchronously: the card that just
            # replaced the old one gets its picture without another download.
            self.signals.loaded.emit(key, size, cached)
            return
        if (key, size) in self._asked:
            return  # already on its way; the cache will catch the rebuilds
        self._asked.add((key, size))
        self._pool.start(CoverTask(key, size, self.signals))

    def forget(self, key: str) -> None:
        """Drop a cover so it is fetched afresh (the book's ISBN changed)."""
        self._asked = {(k, s) for (k, s) in self._asked if k != key}
        self._images = {(k, s): img for (k, s), img in self._images.items() if k != key}


def _device_ratio() -> float:
    """How many physical pixels the screen packs into one logical one.

    1.0 on an ordinary display, 1.5 at 150% scaling, 2.0 on a HiDPI panel.
    Asked of the running app; 1.0 when there is no screen to ask (a headless
    test), which draws exactly as it always did.
    """
    app = QApplication.instance()
    if app is None:
        return 1.0
    screen = app.primaryScreen()
    return screen.devicePixelRatio() if screen is not None else 1.0


def crop_to_size(image: QImage, size: tuple[int, int]) -> QPixmap:
    """A cover filling exactly ``size`` logical pixels, cropped not squashed.

    Book covers come in every shape; stretching one to fit makes the type look
    wrong in a way people notice without knowing why.
    """
    width, height = size
    ratio = _device_ratio()
    # Crop at the physical size, then tell the pixmap its ratio: the layout
    # still sees `size`, but every physical pixel is painted, not stretched.
    pixels_w = round(width * ratio)
    pixels_h = round(height * ratio)
    scaled = image.scaled(
        pixels_w,
        pixels_h,
        Qt.AspectRatioMode.KeepAspectRatioByExpanding,
        Qt.TransformationMode.SmoothTransformation,
    )
    x = max(0, (scaled.width() - pixels_w) // 2)
    y = max(0, (scaled.height() - pixels_h) // 2)
    pixmap = QPixmap.fromImage(scaled.copy(x, y, pixels_w, pixels_h))
    pixmap.setDevicePixelRatio(ratio)
    return pixmap


def placeholder(size: tuple[int, int], text: str = "") -> QPixmap:
    """What to show where a cover would be, when there isn't one.

    Drawn at the screen's real density so its border stays one crisp pixel and
    the book glyph does not go soft. Everything below is worked out in physical
    pixels; the pixmap carries its ratio, so the layout still lays it out at
    ``size``.
    """
    width, height = size
    ratio = _device_ratio()
    pixels_w = round(width * ratio)
    pixels_h = round(height * ratio)

    pixmap = QPixmap(pixels_w, pixels_h)
    pixmap.setDevicePixelRatio(ratio)
    pixmap.fill(colour("cover"))
    painter = QPainter(pixmap)
    try:
        painter.setPen(QPen(colour("cover_edge")))
        painter.drawRect(0, 0, pixels_w - 1, pixels_h - 1)
        if text:
            painter.setPen(QPen(colour("text_soft")))
            # Sized to the space it is filling; the default font draws a book
            # glyph about six pixels across in the middle of a 150x210 panel.
            font = painter.font()
            font.setPixelSize(max(12, round(width * ratio / 5)))
            painter.setFont(font)
            painter.drawText(
                pixmap.rect().adjusted(10, 10, -10, -10),
                int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap),
                text,
            )
    finally:
        painter.end()  # a QPainter left open on a QPixmap corrupts it
    return pixmap
