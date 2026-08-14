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

"""One book's own page.

Only the frame: the cover, the title, and the three panels that do the work --
what the catalogue knows (facts), what you make of it (personal), and where the
book is (lending). Saving lives here, in one place, so that no panel has to
decide for itself what a refused write looks like.

A page in the main window rather than a window of its own. It is opened by the
window, which puts it on the stack and takes it off again when `closed` fires.
"""

from dataclasses import replace

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from books.covers import LARGE_SIZE, crop_to_size, placeholder
from books.facts import FactsPanel
from books.lending_panel import LendingPanel
from books.model import Book
from books.openlibrary import COVER_SIZE_LARGE
from books.personal import PersonalPanel
from books.store import Library
from people.store import Ledger
from shared.icons import dress
from shared.texts import text

# The page is as wide as the window, but a book reads better in a column. Wide
# enough for the cover beside the panels, and no wider.
PAGE_WIDTH = 680


class BookDetail(QWidget):
    """A book, opened."""

    saved = pyqtSignal(str)  # the book's key
    deleted = pyqtSignal(str)  # the book's key
    closed = pyqtSignal()  # done with; the window may take the page away

    def __init__(
        self,
        book: Book,
        library: Library,
        ledger: Ledger,
        cover_loader,
        parent=None,
    ):
        super().__init__(parent)
        # The key, not the book: the library owns the books, and this page
        # asks it for the current one whenever it needs it.
        self.key = book.key
        self.library = library
        self.ledger = ledger
        self.cover_loader = cover_loader
        self._build(book)

        cover_loader.signals.loaded.connect(self._on_cover)
        cover_loader.request(self.key, COVER_SIZE_LARGE)

    # ------------------------------------------------------------ leaving ---
    def go_back(self) -> None:
        """Done with this book.

        The cover is unhooked here rather than on the way out of a `destroyed`
        signal: by then the Python half of this object is already going, and a
        cover arriving in between would reach it.
        """
        self._disconnect()
        self.closed.emit()

    def keyPressEvent(self, event):
        """Escape still leaves, as it did when this was a dialog."""
        if event.key() == Qt.Key.Key_Escape:
            self.go_back()
            return
        super().keyPressEvent(event)

    def _build(self, book: Book) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 24, 28, 20)
        outer.setSpacing(12)

        self.back_button = dress(QPushButton(text("back")), "back")
        self.back_button.clicked.connect(self.go_back)
        outer.addWidget(self.back_button, 0, Qt.AlignmentFlag.AlignLeft)

        # The page is as wide as the window; the book is not. Stretch on both
        # sides rather than letting a one-line Tags box run a thousand pixels.
        middle = QHBoxLayout()
        middle.addStretch(1)
        body = QWidget()
        body.setMaximumWidth(PAGE_WIDTH)
        body.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        middle.addWidget(body, 0)
        middle.addStretch(1)
        outer.addLayout(middle, 1)

        layout = QHBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(18)

        self.cover_label = QLabel()
        self.cover_label.setFixedSize(*LARGE_SIZE)
        self.cover_label.setPixmap(placeholder(LARGE_SIZE, "📖"))
        self.cover_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self.cover_label, 0, Qt.AlignmentFlag.AlignTop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        host = QWidget()
        column = QVBoxLayout(host)
        column.setContentsMargins(0, 0, 8, 0)
        column.setSpacing(6)
        scroll.setWidget(host)
        layout.addWidget(scroll, 1)

        self.title_label = QLabel(book.title)
        self.title_label.setObjectName("pageTitle")
        self.title_label.setTextFormat(Qt.TextFormat.PlainText)
        self.title_label.setWordWrap(True)
        column.addWidget(self.title_label)

        self.personal = PersonalPanel(book, self.library, self._keep)
        self.personal.changed.connect(self._panel_changed)
        column.addWidget(self.personal)

        self.lending = LendingPanel(self.key, self.library, self.ledger)
        self.lending.changed.connect(self._panel_changed)
        column.addWidget(self.lending)

        self.facts = FactsPanel(book, self.library, self._keep)
        self.facts.changed.connect(self._facts_changed)
        column.addWidget(self.facts)
        column.addStretch(1)

        self.delete_button = dress(QPushButton(text("delete_book")), "delete_book")
        self.delete_button.setObjectName("dangerButton")
        self.delete_button.clicked.connect(self._delete)

        # Delete only. There is no "Close" any more: leaving is the Back button
        # at the top, and a second way out at the bottom of a scrolling page is
        # a way out you have to go looking for.
        column.addWidget(self.delete_button, 0, Qt.AlignmentFlag.AlignLeft)

    def _panel_changed(self) -> None:
        self.saved.emit(self.key)

    def _facts_changed(self) -> None:
        """A catalogue edit can change the title, which the window shows at the
        top in its own label -- the facts panel cannot reach it, so it is put
        back in step here."""
        book = self.library.find(self.key)
        if book is not None:
            self.title_label.setText(book.title)
        self.saved.emit(self.key)

    # -------------------------------------------------------------- delete ---
    def _delete(self) -> None:
        """Throw the book away, or just one of its copies.

        The window closes on success: the book it was showing is not there any
        more, and a window onto nothing is a window that lies.
        """
        book = self.library.find(self.key)
        if book is None:
            self.go_back()
            return
        if book.copy_count > 1:
            self._delete_some(book)
            return
        if self._confirmed(book, text("delete_confirm").format(title=book.title)):
            self._remove_whole(book)

    def _delete_some(self, book: Book) -> None:
        """Owning several, "delete" is genuinely two different wishes."""
        box = QMessageBox(self)
        box.setWindowTitle(text("delete_title"))
        box.setText(text("delete_which").format(title=book.title, n=book.copy_count))
        one = box.addButton(text("delete_one_copy"), QMessageBox.ButtonRole.AcceptRole)
        every = box.addButton(
            text("delete_all_copies").format(n=book.copy_count),
            QMessageBox.ButtonRole.DestructiveRole,
        )
        box.addButton(text("cancel"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(one)
        box.exec()

        if box.clickedButton() is one:
            self._drop_one_copy(book)
        elif box.clickedButton() is every and self._confirmed(
            book, text("delete_all_sure")
        ):
            self._remove_whole(book)

    def _confirmed(self, book: Book, question: str) -> bool:
        """Ask, and say first if somebody is holding a copy.

        The loans stay either way -- they are what happened, and they carry the
        title with them -- but somebody still has your book, and being told
        that after it is gone is being told too late.
        """
        out = self.ledger.open_loans_for(self.key)
        if out:
            question += "\n\n" + text("delete_while_out").format(
                names=", ".join(sorted({loan.person_name for loan in out}))
            )
        reply = QMessageBox.question(
            self,
            text("delete_title"),
            question,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return reply == QMessageBox.StandardButton.Yes

    def _drop_one_copy(self, book: Book) -> None:
        out = self.ledger.out_count(self.key)
        if book.copy_count - 1 < out:
            QMessageBox.warning(
                self,
                text("copies_too_few_title"),
                text("copies_too_few").format(out=out),
            )
            return
        if self._keep(replace(book, copies=str(book.copy_count - 1))):
            self.lending.refresh()
            self.saved.emit(self.key)

    def _remove_whole(self, book: Book) -> None:
        if self.library.remove(self.key):
            self.deleted.emit(self.key)
            self.go_back()
            return
        QMessageBox.critical(
            self,
            text("save_failed_title"),
            text("save_failed").format(path=self.library.path),
        )

    def _keep(self, book: Book) -> bool:
        """Save an edited book, and say so if the disk would not have it."""
        if self.library.replace(book):
            return True
        QMessageBox.critical(
            self,
            text("save_failed_title"),
            text("save_failed").format(path=self.library.path),
        )
        return False

    # ---------------------------------------------------------- the cover ---
    def _on_cover(self, key: str, size: str, image) -> None:
        if key == self.key and size == COVER_SIZE_LARGE:
            self.cover_label.setPixmap(crop_to_size(image, LARGE_SIZE))

    def _disconnect(self, *_args) -> None:
        try:
            self.cover_loader.signals.loaded.disconnect(self._on_cover)
        except TypeError:
            pass  # already gone
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
