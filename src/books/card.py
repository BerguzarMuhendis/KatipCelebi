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

"""One book, as it appears in the grid; and the stars, wherever they appear."""

from PyQt6.QtCore import QEvent, Qt, pyqtSignal
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from books.covers import THUMB_SIZE, crop_to_size, placeholder
from books.filters import is_signed
from books.model import Book, parse_rating
from books.reading import NOT_READ, status_of
from shared.texts import text
from shared.theme import colours

STAR_FULL = "★"
STAR_EMPTY = "☆"
SIGNED_BADGE = "✍️"
LENT_BADGE = "👤"


class StarRating(QWidget):
    """Five stars. Clickable when the user is meant to set them."""

    changed = pyqtSignal(int)

    def __init__(self, editable: bool = True, point_size: int = 16, parent=None):
        super().__init__(parent)
        self.editable = editable
        self._rating = 0
        self._stars: list[QLabel] = []

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        for _ in range(5):
            star = QLabel(STAR_EMPTY)
            font = star.font()
            font.setPointSize(max(1, int(point_size)))
            star.setFont(font)
            if editable:
                star.setCursor(Qt.CursorShape.PointingHandCursor)
                star.installEventFilter(self)
            layout.addWidget(star)
            self._stars.append(star)
        layout.addStretch(1)
        self._redraw()

    def rating(self) -> int:
        return self._rating

    def set_rating(self, value: int) -> None:
        self._rating = max(0, min(5, value))
        self._redraw()

    def _redraw(self, hover: int = -1) -> None:
        lit = hover if hover >= 0 else self._rating
        shades = colours()
        for i, star in enumerate(self._stars):
            star.setText(STAR_FULL if i < lit else STAR_EMPTY)
            star.setStyleSheet(
                "color: %s;" % (shades["star"] if i < lit else shades["star_empty"])
            )

    def eventFilter(self, obj, event):
        if self.editable and obj in self._stars:
            index = self._stars.index(obj)
            if event.type() == QEvent.Type.MouseButtonRelease:
                clicked = index + 1
                # Clicking the star you already gave takes the rating off,
                # which is the only way to get back to "not rated".
                self._rating = 0 if clicked == self._rating else clicked
                self._redraw()
                self.changed.emit(self._rating)
                return True
            if event.type() == QEvent.Type.Enter:
                self._redraw(index + 1)
                return True
            if event.type() == QEvent.Type.Leave:
                self._redraw()
                return True
        return super().eventFilter(obj, event)


class BookCard(QFrame):
    """A book in the grid: its cover, who wrote it, what it is called."""

    clicked = pyqtSignal(str)  # the book's key

    def __init__(self, book: Book, lent_out: bool = False, parent=None):
        super().__init__(parent)
        self.book = book
        # Told, not looked up: whether a book is out is the ledger's business,
        # and a card that had to ask would tie the shelf to the people page.
        self.lent_out = lent_out
        self.setObjectName("bookCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedWidth(THUMB_SIZE[0])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(*THUMB_SIZE)
        self.cover_label.setPixmap(placeholder(THUMB_SIZE, "📖"))
        layout.addWidget(self.cover_label)

        # One line, author first: on a shelf you look for who wrote it.
        self.name_label = QLabel(self._one_line())
        self.name_label.setObjectName("cardName")
        self.name_label.setTextFormat(Qt.TextFormat.PlainText)
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.name_label.setWordWrap(True)
        self.name_label.setFixedWidth(THUMB_SIZE[0])
        layout.addWidget(self.name_label)

        self.stars = QLabel()
        self.stars.setTextFormat(Qt.TextFormat.PlainText)
        self.stars.setObjectName("cardStars")
        self.stars.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.stars)

        self.badges = QLabel()
        self.badges.setTextFormat(Qt.TextFormat.PlainText)
        self.badges.setObjectName("cardBadge")
        self.badges.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        layout.addWidget(self.badges)

        self._show_rating()
        self._show_badges()

    def _show_badges(self) -> None:
        """Where the book stands: what you have done with it, and its marks.

        The reading status is spelled out and the rest are symbols, because
        the status is the one a person scans the shelf for -- and a book that
        is unread, here, and unsigned says nothing at all.
        """
        marks, meanings = [], []
        status = status_of(self.book)
        if status != NOT_READ:
            marks.append(text("status_" + status))
        if self.lent_out:
            marks.append(LENT_BADGE)
            meanings.append(text("badge_lent"))
        if is_signed(self.book):
            marks.append(SIGNED_BADGE)
            meanings.append(text("field_signed"))
        self.badges.setText("  •  ".join(marks))
        self.badges.setVisible(bool(marks))
        # The symbols only make sense once you know them, and the card has no
        # room to spell them out.
        self.badges.setToolTip(" • ".join(meanings))

    def _one_line(self) -> str:
        author = self.book.authors.strip()
        title = self.book.title.strip()
        return f"{author} - {title}" if author and title else (title or author)

    def _show_rating(self) -> None:
        stars = parse_rating(self.book.rating)
        # An unrated book shows nothing rather than five empty stars: the grid
        # is for finding a book, and five blanks on every card is just noise.
        self.stars.setText(
            STAR_FULL * stars + STAR_EMPTY * (5 - stars) if stars else ""
        )
        self.stars.setVisible(bool(stars))

    def refresh(self, book: Book, lent_out: bool = False) -> None:
        """Show a book that has just been edited."""
        self.book = book
        self.lent_out = lent_out
        self.name_label.setText(self._one_line())
        self._show_rating()
        self._show_badges()

    def set_cover(self, image: QImage) -> None:
        self.cover_label.setPixmap(crop_to_size(image, THUMB_SIZE))

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.book.key)
        super().mouseReleaseEvent(event)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
