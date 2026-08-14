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

"""What is known about a book: the half that came from the catalogue.

Read-only until you ask to change it. A lookup fills these in, but a lookup
gets things wrong -- a typo in a title, an author's name the wrong way round --
and there was no way to correct one without deleting the book and starting
over. The Edit button opens every field at once; Save writes them, Cancel
forgets them.

It works the same way as the personal panel: it holds the book's key, not the
book, and asks the library for the current one whenever it needs it.
"""

from collections.abc import Callable
from dataclasses import replace

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from books.model import Book
from books.store import Library
from shared.texts import field_label, text

# The catalogue fields, in reading order. Not `key`: that is the book's ISBN,
# which is its identity here -- changing it would be deleting one book and
# adding another, not correcting a typo.
SHOWN = (
    "subtitle",
    "authors",
    "publishers",
    "publish_date",
    "publish_places",
    "edition_name",
    "series",
    "number_of_pages",
    "languages",
    "isbn_10",
    "isbn_13",
    "subjects",
)

# What Edit opens. `title` leads: it is the one most worth being able to fix,
# and the one shown biggest, at the top of the window.
EDITABLE = ("title",) + SHOWN


def _empty(layout) -> None:
    """Take everything out of a layout, widgets and nested layouts alike.

    A plain "delete every widget" loop misses the rows: the heading and the
    Edit button sit in a QHBoxLayout, and a layout is not a widget -- so the
    old row stayed on screen under the new one, two "Book details" deep.
    """
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget is not None:
            widget.setParent(None)
            widget.deleteLater()
        elif item.layout() is not None:
            _empty(item.layout())


class FactsPanel(QWidget):
    """The book as the catalogue knows it, and a way to correct it."""

    changed = pyqtSignal()  # a catalogue field was saved

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
        self._keep = keep
        self._editing = False

        self.column = QVBoxLayout(self)
        self.column.setContentsMargins(0, 0, 0, 0)
        self.column.setSpacing(4)
        self.editors: dict = {}
        self._show()

    def _here(self) -> Book:
        """The book as the library has it now, or a bare one if it has gone."""
        return self.library.find(self.key) or Book(key=self.key)

    def _show(self) -> None:
        self._clear()
        self.editors = {}
        if self._editing:
            self._build_editing()
        else:
            self._build_reading()

    def _clear(self) -> None:
        _empty(self.column)

    # ----------------------------------------------------------- reading ---
    def _build_reading(self) -> None:
        book = self._here()
        row = QHBoxLayout()
        heading = QLabel(text("facts_heading"))
        heading.setObjectName("detailFieldLabel")
        row.addWidget(heading)
        row.addStretch(1)
        self.edit_button = QPushButton(text("facts_edit"))
        self.edit_button.clicked.connect(self._start_editing)
        row.addWidget(self.edit_button)
        self.column.addLayout(row)

        isbn = book.display_isbn
        if isbn:
            self._read_row(field_label("isbn"), isbn)
        for name in SHOWN:
            value = getattr(book, name).strip()
            if value:
                # An empty field is not information, it is clutter.
                self._read_row(field_label(name), value)

    def _read_row(self, heading: str, value: str) -> None:
        label = QLabel(heading)
        label.setObjectName("detailFieldLabel")
        self.column.addWidget(label)
        shown = QLabel(value)
        shown.setWordWrap(True)
        self.column.addWidget(shown)

    # ----------------------------------------------------------- editing ---
    def _build_editing(self) -> None:
        book = self._here()
        heading = QLabel(text("facts_heading"))
        heading.setObjectName("detailFieldLabel")
        self.column.addWidget(heading)

        isbn = book.display_isbn
        if isbn:
            # Shown, not edited: it is the book's identity, not a fact to fix.
            self._read_row(field_label("isbn"), isbn)

        for name in EDITABLE:
            label = QLabel(field_label(name))
            label.setObjectName("detailFieldLabel")
            self.column.addWidget(label)
            editor = QLineEdit(getattr(book, name))
            self.editors[name] = editor
            self.column.addWidget(editor)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        cancel = QPushButton(text("cancel"))
        cancel.clicked.connect(self._stop_editing)
        buttons.addWidget(cancel)
        save = QPushButton(text("save"))
        save.setDefault(True)
        save.clicked.connect(self._save)
        buttons.addWidget(save)
        self.column.addLayout(buttons)
        self.editors["title"].setFocus()

    def _start_editing(self) -> None:
        self._editing = True
        self._show()

    def _stop_editing(self) -> None:
        self._editing = False
        self._show()

    def _save(self) -> None:
        wanted = replace(
            self._here(),
            **{n: e.text().strip() for n, e in self.editors.items()},
        )
        if not wanted.title.strip():
            # A book with no title is a book you cannot find again. Refuse it
            # here rather than let it save into a blank line in the grid.
            self.editors["title"].setFocus()
            return
        if self._keep(wanted):
            self._editing = False
            self._show()
            self.changed.emit()
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
