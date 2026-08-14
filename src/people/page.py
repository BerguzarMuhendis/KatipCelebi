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

"""The People page: who you lend to, and what they have of yours."""

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from people.model import as_date, normalize_id
from people.store import Ledger
from shared.texts import text


class PeoplePage(QWidget):
    """Add people, drop people, and see what each of them is holding."""

    def __init__(self, ledger: Ledger, parent=None):
        super().__init__(parent)
        self.ledger = ledger
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        title = QLabel(text("nav_people"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        self.count_label = QLabel()
        self.count_label.setObjectName("pageSubtitle")
        layout.addWidget(self.count_label)

        add_row = QHBoxLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(text("person_name_hint"))
        self.name_edit.returnPressed.connect(self.add_person)
        add_row.addWidget(self.name_edit, 1)
        self.add_button = QPushButton(text("person_add"))
        self.add_button.setObjectName("primaryButton")  # the main action here
        self.add_button.clicked.connect(self.add_person)
        add_row.addWidget(self.add_button)
        self.remove_button = QPushButton(text("person_remove"))
        self.remove_button.clicked.connect(self.remove_person)
        add_row.addWidget(self.remove_button)
        layout.addLayout(add_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        self.empty_label = QLabel(text("people_empty"))
        self.empty_label.setObjectName("emptyLabel")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.hide()
        layout.addWidget(self.empty_label)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            [
                text("col_person"),
                text("col_trust"),
                text("col_returned"),
                text("col_out"),
                "Id",
            ]
        )
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setMinimumWidth(0)
        self.table.verticalHeader().setMaximumWidth(0)
        self.table.verticalHeader().setDefaultSectionSize(34)
        self.table.setMinimumHeight(220)
        self.table.setColumnWidth(1, 90)
        self.table.setColumnWidth(2, 98)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 120)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setMinimumSectionSize(64)
        self.table.itemSelectionChanged.connect(self._show_history)
        layout.addWidget(self.table, 2)

        self.history_label = QLabel(text("history_none"))
        self.history_label.setObjectName("pageSubtitle")
        layout.addWidget(self.history_label)

        self.history = QTableWidget(0, 3)
        self.history.setHorizontalHeaderLabels(
            [text("col_book"), text("col_lent"), text("col_returned_on")]
        )
        self.history.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.history.verticalHeader().setVisible(False)
        self.history.verticalHeader().setMinimumWidth(0)
        self.history.verticalHeader().setMaximumWidth(0)
        self.history.verticalHeader().setDefaultSectionSize(30)
        self.history.setMinimumHeight(180)
        self.history.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        layout.addWidget(self.history, 1)

    # ------------------------------------------------------------ the list ---
    def refresh(self) -> None:
        """Redraw from the ledger, keeping whoever was selected selected."""
        chosen = self.selected_person_id()
        self.count_label.setText(text("people_count").format(n=len(self.ledger.people)))
        # An empty table is a grid of nothing that explains nothing.
        nobody = not self.ledger.people
        self.empty_label.setVisible(nobody)
        self.table.setVisible(not nobody)
        self.table.setRowCount(len(self.ledger.people))
        for row, person in enumerate(self.ledger.people):
            person_id = normalize_id(person.id)
            out = len(self.ledger.books_out_with(person.id))
            cells = (
                person.name,
                str(self.ledger.trust_score(person.id)),
                str(len(self.ledger.loans_of(person.id)) - out),
                str(out),
                person_id,
            )
            for column, value in enumerate(cells):
                if column == 4:
                    text_value = normalize_id(value)
                    item = QTableWidgetItem(text_value)
                    item.setData(Qt.ItemDataRole.UserRole, text_value)
                    font = item.font()
                    font.setPointSize(10)
                    item.setFont(font)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                else:
                    item = QTableWidgetItem(value)
                self.table.setItem(row, column, item)

        if chosen:
            self.select_person(chosen)
        self._show_history()

    def selected_person_id(self) -> str:
        items = self.table.selectedItems()
        if not items:
            return ""
        row = items[0].row()
        id_item = self.table.item(row, 4)
        if id_item is None:
            return ""
        return normalize_id(
            id_item.data(Qt.ItemDataRole.UserRole) or id_item.text() or ""
        )

    def select_person(self, person_id: str) -> None:
        target = normalize_id(person_id)
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 4)
            if item is not None and (
                normalize_id(item.data(Qt.ItemDataRole.UserRole) or "") == target
                or normalize_id(item.text() or "") == target
            ):
                self.table.selectRow(row)
                return

    # -------------------------------------------------------------- adding ---
    def add_person(self) -> None:
        name = self.name_edit.text()
        if not name.strip():
            self.status_label.setText(text("person_needs_name"))
            return
        if self.ledger.person_named(name) is not None:
            self.status_label.setText(
                text("person_already_known").format(name=name.strip())
            )
            return
        if self.ledger.add_person(name) is None:
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.ledger.people_path),
            )
            return
        self.name_edit.clear()
        self.status_label.setText(text("person_added"))
        self.refresh()

    def remove_person(self) -> None:
        person_id = self.selected_person_id()
        if not person_id:
            self.status_label.setText(text("person_pick_first"))
            return
        person = self.ledger.find_person(person_id)
        out = self.ledger.books_out_with(person_id)
        if out:
            # Their name is written into those loans; removing them would leave
            # the history naming somebody the app no longer has.
            QMessageBox.information(
                self,
                text("person_still_has_books_title"),
                text("person_still_has_books").format(
                    name=person.name,
                    books="\n".join(loan.book_title for loan in out),
                ),
            )
            return
        if (
            QMessageBox.question(
                self,
                text("person_remove_title"),
                text("person_remove_confirm").format(name=person.name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            != QMessageBox.StandardButton.Yes
        ):
            return
        if not self.ledger.remove_person(person_id):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.ledger.people_path),
            )
            return
        self.status_label.setText(text("person_removed"))
        self.refresh()

    # ------------------------------------------------------------ history ---
    def _show_history(self) -> None:
        person_id = self.selected_person_id()
        if not person_id:
            self.history_label.setText(text("history_none"))
            self.history.setRowCount(0)
            return

        person = self.ledger.find_person(person_id)
        loans = list(reversed(self.ledger.loans_of(person_id)))  # newest first
        self.history_label.setText(text("history_of").format(name=person.name))
        self.history.setRowCount(len(loans))
        for row, loan in enumerate(loans):
            cells = (
                loan.book_title,
                as_date(loan.lent_date),
                as_date(loan.return_date) or text("still_out"),
            )
            for column, value in enumerate(cells):
                self.history.setItem(row, column, QTableWidgetItem(value))
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
