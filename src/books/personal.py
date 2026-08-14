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

"""The half of a book that is yours: what you thought of it, and when.

Everything here saves the moment it changes. `keep` is handed in by the window
that owns this panel: it writes the book and says whether the disk took it, so
there is one place that decides what to do when a save fails.
"""

from collections.abc import Callable
from dataclasses import replace

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from books import tags
from books.card import StarRating
from books.filters import SIGNED_VALUE, is_signed
from books.model import Book, parse_rating
from books.reading import (
    NOT_READ,
    READ,
    STATUSES,
    as_date,
    finish_reading,
    format_duration,
    next_step,
    reading_days,
    start_reading,
    status_of,
)
from books.store import Library
from shared.texts import text


class PersonalPanel(QWidget):
    """Rating, signed, reading status and dates, tags, notes."""

    changed = pyqtSignal()

    def __init__(
        self,
        book: Book,
        library: Library,
        keep: Callable[[Book], bool],
        parent=None,
    ):
        super().__init__(parent)
        self.key = book.key
        self.library = library
        self._keep_book = keep

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)
        self._build_rating(column, book)
        self._build_reading(column, book)
        self._build_tags(column, book)
        self._build_notes(column, book)

    def _heading(self, column, key: str) -> None:
        label = QLabel(text(key))
        label.setObjectName("detailFieldLabel")
        column.addWidget(label)

    def _keep(self, book: Book) -> bool:
        if self._keep_book(book):
            self.changed.emit()
            return True
        return False

    # ------------------------------------------------------ rating, signed ---
    def _build_rating(self, column, book: Book) -> None:
        self._heading(column, "field_rating")
        self.stars = StarRating(editable=True, point_size=18)
        self.stars.set_rating(parse_rating(book.rating))
        self.stars.changed.connect(self._save_rating)
        column.addWidget(self.stars)

        self.signed_check = QCheckBox(text("field_signed"))
        self.signed_check.setChecked(is_signed(book))
        self.signed_check.toggled.connect(self._save_signed)
        column.addWidget(self.signed_check)

    def _save_rating(self, stars: int) -> None:
        """Stars save themselves: a Save button for one number is a button
        nobody wants to press."""
        book = self.library.find(self.key)
        if book is None:
            return
        if not self._keep(replace(book, rating=str(stars) if stars else "")):
            # The write failed, so the library still holds the old rating. Show
            # that, not a number the disk has never heard of.
            self.stars.set_rating(parse_rating(book.rating))

    def _save_signed(self, ticked: bool) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        if not self._keep(replace(book, signed=SIGNED_VALUE if ticked else "")):
            self.signed_check.blockSignals(True)
            self.signed_check.setChecked(is_signed(book))
            self.signed_check.blockSignals(False)

    # ------------------------------------------------------------- reading ---
    def _build_reading(self, column, book: Book) -> None:
        self._heading(column, "field_status")
        self.status_combo = QComboBox()
        for status in STATUSES:
            self.status_combo.addItem(text("status_" + status), status)
        self._show_status(book)
        self.status_combo.activated.connect(self._save_status)
        column.addWidget(self.status_combo)

        self.reading_label = QLabel()
        self.reading_label.setWordWrap(True)
        column.addWidget(self.reading_label)
        self.reading_button = QPushButton()
        self.reading_button.setObjectName("primaryButton")  # the page's action
        self.reading_button.clicked.connect(self._reading_step)
        column.addWidget(self.reading_button)
        self._refresh_reading(book)

    def _refresh_reading(self, book: Book) -> None:
        """The sentence about where the book is, and what the button offers."""
        status = status_of(book)
        if status == "reading" and book.started_date:
            said = text("reading_since").format(date=as_date(book.started_date))
        elif status == READ and book.finished_date:
            span = reading_days(book)
            said = (
                text("reading_finished_on").format(date=as_date(book.finished_date))
                if span is None
                else text("reading_finished").format(
                    date=as_date(book.finished_date),
                    duration=format_duration(span),
                )
            )
        else:
            said = text("reading_not_started")
        self.reading_label.setText(said)

        if status == READ:
            self.reading_button.setText(text("reading_again"))
        elif next_step(book) == READ:
            self.reading_button.setText(text("reading_finish"))
        else:
            self.reading_button.setText(text("reading_start"))

    def _reading_step(self) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        moved = finish_reading(book) if next_step(book) == READ else start_reading(book)
        if self._keep(moved):
            self._show_status(moved)
            self._refresh_reading(moved)

    def _show_status(self, book: Book) -> None:
        index = self.status_combo.findData(status_of(book))
        self.status_combo.blockSignals(True)
        self.status_combo.setCurrentIndex(max(index, 0))
        self.status_combo.blockSignals(False)

    def _save_status(self, *_args) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        moved = replace(book, status=self.status_combo.currentData() or NOT_READ)
        if self._keep(moved):
            self._refresh_reading(moved)
        else:
            self._show_status(book)

    # ---------------------------------------------------------------- tags ---
    def _build_tags(self, column, book: Book) -> None:
        self._heading(column, "field_tags")
        self.tags_edit = QLineEdit(tags.show(book.tags))
        self.tags_edit.setPlaceholderText(text("tags_hint"))
        self.tags_edit.editingFinished.connect(self._save_tags)
        column.addWidget(self.tags_edit)

    def _save_tags(self) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        wanted = tags.store(self.tags_edit.text())
        if wanted == book.tags:
            # editingFinished fires on every focus change, not only on an edit.
            return
        if self._keep(replace(book, tags=wanted)):
            self.tags_edit.setText(tags.show(wanted))
        else:
            self.tags_edit.setText(tags.show(book.tags))

    # --------------------------------------------------------------- notes ---
    def _build_notes(self, column, book: Book) -> None:
        self._heading(column, "field_notes")
        self.notes_edit = QTextEdit()
        # setPlainText, never QTextEdit(book.notes): that constructor reads its
        # argument as HTML, and HTML folds every run of whitespace into one
        # space. Notes came back with their paragraphs collapsed into a single
        # line -- and saving then wrote that line over the real ones.
        self.notes_edit.setPlainText(book.notes)
        self.notes_edit.setPlaceholderText(text("notes_hint"))
        self.notes_edit.setFixedHeight(110)
        self.notes_edit.textChanged.connect(self._preview_notes)
        column.addWidget(self.notes_edit)

        self._heading(column, "notes_preview")
        self.notes_preview = QLabel()
        self.notes_preview.setWordWrap(True)
        self.notes_preview.setTextFormat(Qt.TextFormat.MarkdownText)
        column.addWidget(self.notes_preview)

        self.notes_save = QPushButton(text("save_notes"))
        self.notes_save.clicked.connect(self._save_notes)
        column.addWidget(self.notes_save)
        self._preview_notes()

    def _preview_notes(self) -> None:
        self.notes_preview.setText(self.notes_edit.toPlainText())

    def _save_notes(self) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        if not self._keep(replace(book, notes=self.notes_edit.toPlainText())):
            self.notes_edit.setPlainText(book.notes)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
