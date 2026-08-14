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

"""The Add Book page: type an ISBN, or type the whole book in yourself."""

import logging
from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import QObject, QRunnable, Qt, QThreadPool, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from books import tags
from books.card import StarRating
from books.excel import (
    TEMPLATE_DEFAULT_NAME,
    FileTooLarge,
    read_template,
    write_template,
)
from books.filters import SIGNED_VALUE
from books.model import (
    ISBN_LENGTH,
    ISBN_OK,
    Book,
    check_isbn,
    is_valid_isbn,
    normalize_isbn,
)
from books.openlibrary import SUBMIT_FAILED, SUBMIT_OK, fetch_book, submit_book
from books.reading import STATUSES
from books.store import Library
from shared import credentials
from shared.icons import dress
from shared.texts import field_label, text
from books.import_worker import (
    LookupSignals,
    LookupTask,
    ImportSignals,
    ImportTask,
    SubmitSignals,
    SubmitTask,
)

logger = logging.getLogger("katipcelebi")

# The fields the form offers, in the blocks they are read in. `key` is not
# among them: it is the app's, not the user's, and a book without an ISBN gets
# one of its own. Twenty-odd boxes in one column is a wall; these are the four
# things somebody is actually looking for.
FORM_SECTIONS = (
    (
        "section_basic",
        (
            "title",
            "subtitle",
            "authors",
            "publishers",
            "publish_date",
            "publish_places",
            "edition_name",
            "series",
        ),
    ),
    (
        "section_physical",
        ("number_of_pages", "languages", "isbn_10", "isbn_13"),
    ),
    ("section_content", ("subjects",)),
)

FORM_FIELDS = tuple(name for _heading, names in FORM_SECTIONS for name in names)





class AddBookPage(QWidget):
    """Look a book up, check it over, keep it."""

    book_added = pyqtSignal(str)  # the book's key

    def __init__(self, library: Library, parent=None):
        super().__init__(parent)
        self.library = library
        self.fields: dict[str, QLineEdit] = {}
        self._signals: LookupSignals | None = None
        self._looking_up = False
        # The ISBN of the last book a lookup failed to find. A book saved by
        # hand under this key is the one worth offering to Open Library.
        self._not_found_isbn = ""
        self._build()
        self.refresh_tags()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 20)
        layout.setSpacing(12)

        self.title_label = QLabel(text("nav_add"))
        self.title_label.setObjectName("pageTitle")
        layout.addWidget(self.title_label)

        isbn_row = QHBoxLayout()
        isbn_row.addWidget(QLabel(text("isbn_label")))
        self.isbn_edit = QLineEdit()
        self.isbn_edit.setPlaceholderText(text("isbn_hint"))
        self.isbn_edit.returnPressed.connect(self.look_up)
        isbn_row.addWidget(self.isbn_edit, 1)
        self.fetch_button = dress(QPushButton(text("fetch")), "fetch")
        self.fetch_button.clicked.connect(self.look_up)
        isbn_row.addWidget(self.fetch_button)
        layout.addLayout(isbn_row)

        bulk_row = QHBoxLayout()
        self.template_button = dress(
            QPushButton(text("template_button")), "template_button"
        )
        self.template_button.clicked.connect(self.save_template)
        bulk_row.addWidget(self.template_button)
        self.import_button = dress(QPushButton(text("import_button")), "import_button")
        self.import_button.clicked.connect(self.import_list)
        bulk_row.addWidget(self.import_button)
        bulk_row.addStretch(1)
        layout.addLayout(bulk_row)

        self.status_label = QLabel()
        self.status_label.setObjectName("statusLabel")
        layout.addWidget(self.status_label)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        host = QWidget()
        # One form for every block, not one per block: a QFormLayout sizes its
        # label column to its own longest label, so four of them would step the
        # boxes in and out at each heading.
        form = QFormLayout(host)
        form.setContentsMargins(0, 0, 8, 0)
        form.setSpacing(10)
        for heading, names in FORM_SECTIONS:
            fields_form = self._section(form, heading)
            for name in names:
                edit = QLineEdit()
                self.fields[name] = edit
                fields_form.addRow(QLabel(field_label(name) + ":"), edit)
        self._build_personal(form)
        scroll.setWidget(host)
        layout.addWidget(scroll, 1)

        buttons = QHBoxLayout()
        buttons.addStretch(1)
        self.clear_button = dress(QPushButton(text("clear")), "clear")
        self.clear_button.clicked.connect(self.clear_form)
        buttons.addWidget(self.clear_button)
        self.save_button = dress(QPushButton(text("save")), "save")
        self.save_button.setObjectName("primaryButton")  # the one filled action
        self.save_button.setDefault(True)
        self.save_button.clicked.connect(self.save_book)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)

    def _section(self, form, key: str) -> QFormLayout:
        """Create a collapsible section with a header and a form body."""
        section = QWidget()
        section_layout = QVBoxLayout(section)
        section_layout.setContentsMargins(0, 0, 0, 0)
        section_layout.setSpacing(6)

        header = QToolButton()
        header.setText(text(key))
        header.setCheckable(True)
        header.setChecked(True)
        header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        header.setAutoRaise(True)
        header.setArrowType(Qt.ArrowType.DownArrow)
        header.setObjectName("detailFieldLabel")
        section_layout.addWidget(header)

        body = QWidget()
        body_layout = QFormLayout(body)
        body_layout.setContentsMargins(16, 0, 8, 0)
        body_layout.setSpacing(10)
        section_layout.addWidget(body)

        def _sync_arrow(checked: bool) -> None:
            header.setArrowType(
                Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
            )

        header.toggled.connect(_sync_arrow)
        header.toggled.connect(body.setVisible)
        form.addRow(section)
        return body_layout

    def _build_personal(self, form) -> None:
        """What you make of the book, rather than what the catalogue knows.

        None of it comes from a lookup, so it all sits below what does. It is
        here so that a book can be finished being entered in one go, instead of
        being saved and then opened again to say you liked it.
        """
        personal_form = self._section(form, "section_personal")

        self.stars = StarRating(editable=True, point_size=18)
        personal_form.addRow(QLabel(text("field_rating") + ":"), self.stars)

        self.status_combo = QComboBox()
        for status in STATUSES:
            self.status_combo.addItem(text("status_" + status), status)
        personal_form.addRow(QLabel(text("field_status") + ":"), self.status_combo)

        tags_row = QHBoxLayout()
        tags_row.setContentsMargins(0, 0, 0, 0)
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText(text("tags_hint"))
        tags_row.addWidget(self.tags_edit, 1)
        # A box with nothing but a placeholder does not say what a tag is
        # meant to be, and a new library has no tags of its own to copy.
        self.tags_pick = QComboBox()
        self.tags_pick.setMinimumWidth(150)
        self.tags_pick.activated.connect(self._add_picked_tag)
        tags_row.addWidget(self.tags_pick)
        personal_form.addRow(QLabel(text("field_tags") + ":"), tags_row)

        self.signed_check = QCheckBox(text("field_signed"))
        personal_form.addRow("", self.signed_check)

        notes_form = self._section(form, "field_notes")
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(text("notes_hint"))
        self.notes_edit.setFixedHeight(90)
        self.notes_edit.textChanged.connect(self._preview_notes)
        notes_form.addRow(self.notes_edit)

        preview_form = self._section(form, "notes_preview")
        self.notes_preview = QLabel()
        self.notes_preview.setWordWrap(True)
        self.notes_preview.setTextFormat(Qt.TextFormat.MarkdownText)
        preview_form.addRow(self.notes_preview)

    def _preview_notes(self) -> None:
        self.notes_preview.setText(self.notes_edit.toPlainText())

    # ---------------------------------------------------------------- tags ---
    def refresh_tags(self) -> None:
        """Reload what the picker offers. The library's tags change."""
        self.tags_pick.blockSignals(True)
        self.tags_pick.clear()
        self.tags_pick.addItem(text("tags_pick"), "")
        for tag in tags.suggestions(self.library.books):
            self.tags_pick.addItem(tags.display(tag), tag)
        self.tags_pick.setCurrentIndex(0)
        self.tags_pick.blockSignals(False)

    def _add_picked_tag(self, *_args) -> None:
        """Add the chosen tag to whatever is already typed.

        Added, not replaced: the box holds a list, and picking a second tag is
        asking for both. Picking the same one twice is not -- but that is
        `store`'s rule, not one to write again here. It also settles every tag
        to its canonical form, which is why the box cannot simply be compared
        against: it reads "Poetry" where the picker holds "poetry".
        """
        chosen = self.tags_pick.currentData()
        self.tags_pick.setCurrentIndex(0)
        if not chosen:
            return
        typed = self.tags_edit.text().strip()
        both = (typed + ", " + chosen) if typed else chosen
        self.tags_edit.setText(tags.show(tags.store(both)))

    # ------------------------------------------------------------- lookup ---
    def _isbn_complaint(self) -> str:
        """What is wrong with what is in the ISBN box, in words.

        Empty when there is nothing wrong with it.
        """
        why, count = check_isbn(self.isbn_edit.text())
        if why == ISBN_OK:
            return ""
        if why == ISBN_LENGTH:
            return text("isbn_length").format(n=count)
        return text("isbn_" + why)

    def look_up(self) -> None:
        complaint = self._isbn_complaint()
        if complaint:
            QMessageBox.critical(self, text("isbn_invalid_title"), complaint)
            return
        isbn = self.isbn_edit.text().strip()
        if self._looking_up:
            # The button is disabled while one is in flight, but Enter in the
            # ISBN box is not: holding it down started a worker per keystroke.
            return

        self._looking_up = True
        self.fetch_button.setEnabled(False)
        self.status_label.setText(text("fetching"))

        asked_about = normalize_isbn(isbn)
        signals = LookupSignals()
        signals.done.connect(self._lookup_done)
        self._signals = signals  # keep it alive until it has fired
        QThreadPool.globalInstance().start(LookupTask(asked_about, signals))

    def _lookup_done(self, book: Book | None, asked_about: str) -> None:
        self._looking_up = False
        self.fetch_button.setEnabled(True)
        # The box stays editable while we wait, so the answer may be about a
        # book the user has already moved on from.
        if normalize_isbn(self.isbn_edit.text()) != asked_about:
            logger.info(
                "Ignoring the answer about %s; the box says something else",
                asked_about,
            )
            return
        if book is None:
            self.status_label.setText(text("fetch_not_found"))
            # Remember it: if the user goes on to type this book in by hand and
            # save it, that is exactly the book Open Library did not have and
            # might like to.
            self._not_found_isbn = asked_about
            return
        self.status_label.setText(text("fetch_ok"))
        self.isbn_edit.setText(book.key)
        for name, edit in self.fields.items():
            edit.setText(getattr(book, name))
        # Tags come from the catalogue's own subjects. Merged, not assigned:
        # everything else on this form is Open Library's to fill in, but a
        # tag the user has already typed is theirs.
        typed = tags.split_tags(tags.store(self.tags_edit.text()))
        found = tags.split_tags(book.tags)
        merged = typed + [t for t in found if t not in typed]
        self.tags_edit.setText(tags.show(", ".join(merged)))

    # ------------------------------------------------------ the whole list ---
    def save_template(self) -> None:
        """An empty sheet with one column, for the user to paste ISBNs into."""
        suggested = str(Path.home() / TEMPLATE_DEFAULT_NAME)
        chosen, _ = QFileDialog.getSaveFileName(
            self, text("template_button"), suggested, "Excel (*.xlsx)"
        )
        if not chosen:
            return
        if write_template(Path(chosen)):
            self.status_label.setText(text("template_done").format(path=chosen))
        else:
            self.status_label.setText(text("template_failed"))

    def import_list(self) -> None:
        chosen, _ = QFileDialog.getOpenFileName(
            self, text("import_button"), str(Path.home()), "Excel (*.xlsx)"
        )
        if not chosen:
            return
        try:
            isbns = read_template(Path(chosen))
        except FileTooLarge:
            # The file is fine; it is just too big to read. Say that, and not
            # the "could not read it" sentence -- that one would send somebody
            # looking for a broken file.
            QMessageBox.critical(
                self,
                text("import_too_large_title"),
                text("import_too_large"),
            )
            return
        if isbns is None:
            QMessageBox.critical(
                self,
                text("import_unreadable_title"),
                text("import_unreadable"),
            )
            return
        if not isbns:
            QMessageBox.information(
                self, text("import_none_title"), text("import_none")
            )
            return

        self.import_button.setEnabled(False)
        self.status_label.setText(text("importing").format(n=len(isbns)))
        signals = ImportSignals()
        signals.done.connect(self._import_done)
        self._import_signals = signals  # keep it alive until it has fired
        QThreadPool.globalInstance().start(ImportTask(isbns, signals))

    def _import_done(self, found: list, missing: list, network_problem: bool) -> None:
        self.import_button.setEnabled(True)
        if network_problem:
            QMessageBox.critical(
                self,
                text("import_network_error_title"),
                text("import_network_error"),
            )
            # Continue to show what we did manage to find and which are missing,
            # rather than swallow the whole result.
        added, duplicates = [], []
        for book in found:
            if self.library.find(book.key) is not None:
                duplicates.append(book)
                continue
            if self.library.add(book):
                added.append(book)
            else:
                # The disk said no. Stop rather than march on: the rest would
                # fail the same way, and one dialog is enough.
                QMessageBox.critical(
                    self,
                    text("save_failed_title"),
                    text("save_failed").format(path=self.library.path),
                )
                break

        self.status_label.clear()
        said = text("import_done").format(
            added=len(added),
            duplicates=len(duplicates),
            not_found=len(missing),
        )
        if missing:
            # Naming them, not just counting them: "not found: 2" out of a
            # hundred leaves somebody to work out which two by hand, and the
            # whole point of the list was not doing that.
            said += "\n\n" + text("import_not_found").format(isbns="\n".join(missing))
        QMessageBox.information(self, text("import_done_title"), said)
        if added:
            self.book_added.emit(added[-1].key)

    # ------------------------------------------------------------- saving ---
    def clear_form(self) -> None:
        self.isbn_edit.clear()
        for edit in self.fields.values():
            edit.clear()
        self.signed_check.setChecked(False)
        self.tags_edit.clear()
        self.stars.set_rating(0)
        self.status_combo.setCurrentIndex(0)
        self.notes_edit.clear()
        self.status_label.clear()

    def _form_book(self) -> Book:
        isbn = normalize_isbn(self.isbn_edit.text())
        book = Book(key=isbn if is_valid_isbn(isbn) else Book.new_local_key())
        for name, edit in self.fields.items():
            setattr(book, name, edit.text().strip())
        book.signed = SIGNED_VALUE if self.signed_check.isChecked() else ""
        book.tags = tags.store(self.tags_edit.text())
        book.rating = str(self.stars.rating()) if self.stars.rating() else ""
        book.status = self.status_combo.currentData() or ""
        book.notes = self.notes_edit.toPlainText()
        return book

    def save_book(self) -> None:
        # An ISBN typed but wrong used to be dropped on the floor: the book
        # saved with a made-up key, no ISBN, no cover, no way to notice it was
        # a duplicate -- and the user watching it say "Saved". A box with
        # something in it that is not an ISBN is a question, not an answer.
        if self.isbn_edit.text().strip():
            complaint = self._isbn_complaint()
            if complaint:
                QMessageBox.critical(
                    self,
                    text("isbn_refused_title"),
                    text("isbn_refused").format(why=complaint),
                )
                return

        book = self._form_book()
        if not book.title:
            self.status_label.setText(text("title_required"))
            return

        # Only a real ISBN identifies a book well enough to call it a
        # duplicate; two hand-typed books with no ISBN are two books.
        if not book.is_local_key:
            existing = self.library.find(book.key)
            if existing is not None:
                self._one_more_copy(existing)
                return

        if not self.library.add(book):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.library.path),
            )
            return

        logger.info("Added %s (%s)", book.key, book.title)
        self.status_label.setText(text("saved"))
        offer = self._not_found_isbn == book.key and not book.is_local_key
        self.clear_form()
        self.book_added.emit(book.key)
        if offer:
            # This is the book the catalogue did not have. Offer to send it,
            # after the save, so a "no" or a network problem never stands
            # between the user and their own library.
            self._not_found_isbn = ""
            self._offer_submission(book)

    # ----------------------------------------------- to open library ---
    def _offer_submission(self, book: Book) -> None:
        """Ask whether to send a not-found book to Open Library, and do it."""
        yes = QMessageBox.question(
            self,
            text("ol_offer_title"),
            text("ol_offer").format(title=book.title),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if yes != QMessageBox.StandardButton.Yes:
            return

        signin = self._ask_to_sign_in()
        if signin is None:
            return
        username, password = signin

        self.status_label.setText(text("ol_sending"))
        signals = SubmitSignals()
        signals.done.connect(self._submission_done)
        self._submit_signals = signals  # keep it alive until it has fired
        QThreadPool.globalInstance().start(
            SubmitTask(book, username, password, signals)
        )

    def _ask_to_sign_in(self):
        """The Open Library sign-in, from the store or from the user.

        Returns (username, password), or None if the user backed out. The
        password is asked for even when it is remembered -- it is never shown,
        only sent -- so the box below is the one place it lives in the open,
        for as long as the dialog is on screen.
        """
        remembered = credentials.load()
        user_default = remembered[0] if remembered else ""

        username, ok = QInputDialog.getText(
            self,
            text("ol_signin_title"),
            text("ol_username"),
            text=user_default,
        )
        if not ok or not username.strip():
            return None
        password, ok = QInputDialog.getText(
            self,
            text("ol_signin_title"),
            text("ol_password"),
            QLineEdit.EchoMode.Password,
            remembered[1] if remembered and remembered[0] == username else "",
        )
        if not ok or not password:
            return None

        if credentials.can_remember():
            keep = QMessageBox.question(
                self,
                text("ol_remember_title"),
                text("ol_remember"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )
            if keep == QMessageBox.StandardButton.Yes:
                credentials.save(username.strip(), password)
            else:
                credentials.forget()
        return username.strip(), password

    def _submission_done(self, reason: str) -> None:
        if reason == SUBMIT_OK:
            self.status_label.clear()
            QMessageBox.information(self, text("ol_thanks_title"), text("ol_thanks"))
            return
        self.status_label.clear()
        QMessageBox.warning(self, text("ol_failed_title"), text("ol_" + reason))

    def _one_more_copy(self, existing: Book) -> None:
        """The same ISBN twice is the same book twice, not two books.

        Nothing on the form is written over the one already saved: what is
        being said is "there are two of these now", and the rating and notes on
        the book are about the work, which has not changed.
        """
        wanted = replace(existing, copies=str(existing.copy_count + 1))
        if not self.library.replace(wanted):
            QMessageBox.critical(
                self,
                text("save_failed_title"),
                text("save_failed").format(path=self.library.path),
            )
            return
        logger.info("Now %d copies of %s", wanted.copy_count, existing.key)
        QMessageBox.information(
            self,
            text("copies_added_title"),
            text("copies_added").format(title=existing.title, n=wanted.copy_count),
        )
        self.clear_form()
        self.book_added.emit(existing.key)
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
