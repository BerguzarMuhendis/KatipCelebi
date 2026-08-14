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

"""Where a book is: how many you have, and who is holding them."""

from dataclasses import replace

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from books.model import MAX_COPIES, Book
from books.store import Library
from people.model import as_date
from people.store import Ledger
from shared.texts import text


class LendingPanel(QWidget):
    """How many copies there are, which of them are out, and with whom.

    A book you own two of can be in two people's hands at once, so every open
    loan gets its own row and its own way back. Owning one -- which is nearly
    every book -- still reads as one line and one button.
    """

    changed = pyqtSignal()

    def __init__(self, key: str, library: Library, ledger: Ledger, parent=None):
        super().__init__(parent)
        self.key = key
        self.library = library
        self.ledger = ledger
        self._loan_rows: list[QWidget] = []

        column = QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)

        heading = QLabel(text("field_lending"))
        heading.setObjectName("detailFieldLabel")
        column.addWidget(heading)

        copies_row = QHBoxLayout()
        copies_row.addWidget(QLabel(text("field_copies") + ":"))
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, MAX_COPIES)
        self.copies_spin.setValue(self._book_copies())
        self.copies_spin.valueChanged.connect(self._save_copies)
        copies_row.addWidget(self.copies_spin)
        copies_row.addStretch(1)
        column.addLayout(copies_row)

        self.lending_label = QLabel()
        self.lending_label.setWordWrap(True)
        column.addWidget(self.lending_label)

        # Every open loan draws a row into here.
        self.loans_host = QWidget()
        self.loans_column = QVBoxLayout(self.loans_host)
        self.loans_column.setContentsMargins(0, 0, 0, 0)
        self.loans_column.setSpacing(4)
        column.addWidget(self.loans_host)

        self.lend_row = QWidget()
        inner = QHBoxLayout(self.lend_row)
        inner.setContentsMargins(0, 0, 0, 0)
        self.person_combo = QComboBox()
        # Editable: a name that is not on the list yet is a name, not a
        # detour to another page and back.
        self.person_combo.setEditable(True)
        self.person_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.person_combo.lineEdit().setPlaceholderText(text("lend_who"))
        inner.addWidget(self.person_combo, 1)
        self.lend_button = QPushButton(text("lend"))
        self.lend_button.clicked.connect(self._lend)
        inner.addWidget(self.lend_button)
        column.addWidget(self.lend_row)
        self.refresh()

    # ------------------------------------------------------------- reading ---
    def _book(self) -> Book:
        """The book as the library has it now, or a bare one if it has gone."""
        return self.library.find(self.key) or Book(key=self.key)

    def _book_copies(self) -> int:
        return self._book().copy_count

    def refresh(self) -> None:
        """Redraw from the ledger.

        What is out is never a guess -- it is asked.
        """
        out = self.ledger.open_loans_for(self.key)
        copies = self._book_copies()

        self._show_copies(copies)
        self._show_loans(out)
        self._show_sentence(len(out), copies)
        self._show_lend_row(len(out) < copies)

    def _show_copies(self, copies: int) -> None:
        self.copies_spin.blockSignals(True)
        self.copies_spin.setValue(copies)
        self.copies_spin.blockSignals(False)

    def _show_loans(self, out: list) -> None:
        for row in self._loan_rows:
            row.setParent(None)
            row.deleteLater()
        self._loan_rows = []
        for loan in out:
            self._loan_rows.append(self._loan_row(loan))

    def _loan_row(self, loan) -> QWidget:
        row = QWidget()
        inner = QHBoxLayout(row)
        inner.setContentsMargins(0, 0, 0, 0)
        who = QLabel(
            text("out_with").format(name=loan.person_name, date=as_date(loan.lent_date))
        )
        who.setWordWrap(True)
        inner.addWidget(who, 1)
        button = QPushButton(text("take_back"))
        # The loan's own id, not the book's key: with two copies out, "give it
        # back" would otherwise have to guess which one came home.
        button.clicked.connect(
            lambda _checked=False, loan_id=loan.id: self._take_back(loan_id)
        )
        inner.addWidget(button)
        self.loans_column.addWidget(row)
        return row

    def _show_sentence(self, out: int, copies: int) -> None:
        """One line saying where the book stands.

        Empty when the rows already say it all.
        """
        if out == 0:
            said = text("at_home") if copies == 1 else text("all_here").format(n=copies)
        elif copies == 1:
            said = ""  # the single loan row already names who has it
        elif out == copies:
            said = text("all_out").format(n=copies)
        else:
            said = text("some_here").format(here=copies - out, total=copies)
        self.lending_label.setText(said)
        self.lending_label.setVisible(bool(said))

    def _show_lend_row(self, a_copy_is_here: bool) -> None:
        if not a_copy_is_here:
            self.lend_row.setVisible(False)
            return
        self.lend_row.setVisible(True)
        self.person_combo.clear()
        for person in self.ledger.people:
            self.person_combo.addItem(person.name, person.id)
        # Always: a name can be typed straight in, so there is nobody this
        # button cannot lend to.
        self.lend_button.setEnabled(True)
        self.person_combo.setCurrentIndex(-1 if not self.ledger.people else 0)

    # ------------------------------------------------------------- writing ---
    def _save_copies(self, wanted: int) -> None:
        book = self.library.find(self.key)
        if book is None:
            return
        out = self.ledger.out_count(self.key)
        if wanted < out:
            # Those copies are in somebody's hands. Owning fewer than you have
            # lent out is not a thing that can be true.
            QMessageBox.warning(
                self,
                text("copies_too_few_title"),
                text("copies_too_few").format(out=out),
            )
            self._show_copies(book.copy_count)
            return
        if wanted == book.copy_count:
            return
        if self.library.replace(replace(book, copies=str(wanted))):
            self.refresh()
            self.changed.emit()
            return
        QMessageBox.critical(
            self,
            text("save_failed_title"),
            text("save_failed").format(path=self.library.path),
        )
        self._show_copies(book.copy_count)

    def _lend(self) -> None:
        book = self.library.find(self.key)
        if book is None or not self.ledger.can_lend(book):
            # Every copy is already out, so there is nothing here to hand over.
            # Not a refused write: saying "the disk would not have it" here
            # would send somebody looking for a problem that is not there.
            self.refresh()
            return
        person = self._whoever_is_named()
        if person is None:
            self.lending_label.setText(text("lend_pick_person"))
            self.lending_label.setVisible(True)
            return
        self._done(self.ledger.lend(book, person))

    def _whoever_is_named(self):
        """The person the combo names, making them up if they are new.

        The box is editable, so somebody handing a book to a friend who is not
        on the list yet can just type the name -- rather than leave the book,
        go to the People page, add them, and come back.
        """
        chosen = self.ledger.find_person(self.person_combo.currentData() or "")
        if chosen is not None:
            return chosen

        typed = self.person_combo.currentText()
        known = self.ledger.person_named(typed)
        if known is not None:
            # They typed a name that is already on the list. Use that one:
            # a second Ali is two people as far as the history is concerned.
            return known
        return self.ledger.add_person(typed)

    def _take_back(self, loan_id: str) -> None:
        self._done(self.ledger.take_back(loan_id))

    def _done(self, worked: bool) -> None:
        if not worked:
            QMessageBox.critical(
                self,
                text("lend_failed_title"),
                text("lend_failed").format(path=self.ledger.loans_path),
            )
        self.refresh()
        self.changed.emit()
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
