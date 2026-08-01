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

"""The library: the books, and the file they live in."""

import logging
from pathlib import Path

from books.model import Book
from shared.paths import library_path
from shared.storage import DataFileDamaged, read_rows, write_rows

logger = logging.getLogger("katipcelebi")


class Library:
    """Every book the user has, and the one file that holds them.

    Memory and disk are kept in step by construction: nothing changes the list
    without going through here, and nothing here changes the list unless the
    write succeeded. The old version let a failed save leave the two
    disagreeing -- the window showed a book that was not in the file.
    """

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.books: list[Book] = []
        # Set when the file was unreadable and had to be moved aside, so the
        # window can say where the user's books went.
        self.rescued_to: Path | None = None
        self.skipped_entries = 0

    @property
    def path(self) -> Path:
        return library_path(self.folder)

    # ------------------------------------------------------------- loading ---
    def load(self) -> None:
        """Read the library. An unreadable file leaves us empty but says so."""
        self.rescued_to = None
        self.skipped_entries = 0
        try:
            result = read_rows(self.path)
        except DataFileDamaged as damage:
            self.rescued_to = damage.rescued_to
            self.books = []
            return

        self.skipped_entries = result.skipped
        books = []
        for row in result.rows:
            try:
                books.append(Book.from_dict(row))
            except TypeError:
                self.skipped_entries += 1
        self.books = books

        if self._give_everyone_a_key():
            # Written back now, while we know they are unique. Left to chance,
            # two books would answer to the same key for the rest of the
            # session.
            self.save()
        logger.info("Loaded %d book(s) from %s", len(self.books), self.path)

    def _give_everyone_a_key(self) -> bool:
        """Make sure no two books answer to the same name. True if any changed.

        A key is a book's identity everywhere in the app. A file written by
        hand can easily have two books with no ISBN, or the same one twice;
        without this, one of them disappears from the grid and edits to the
        other land on the wrong book.
        """
        seen, changed = set(), False
        for book in self.books:
            key = book.key.strip()
            if not key or key in seen:
                book.key = Book.new_local_key()
                changed = True
            seen.add(book.key)
        return changed

    # ------------------------------------------------------------- saving ---
    def save(self) -> bool:
        return write_rows(self.path, [book.to_dict() for book in self.books])

    def find(self, key: str) -> Book | None:
        return next((b for b in self.books if b.key == key), None)

    def add(self, book: Book) -> bool:
        """Add a book and write the library. False leaves nothing changed.

        The book is put in only if the file took it, so a failed write never
        leaves the window showing something the disk does not have.
        """
        if not book.key:
            book.key = Book.new_local_key()
        self.books.append(book)
        if self.save():
            return True
        self.books.pop()
        return False

    def remove(self, key: str) -> bool:
        book = self.find(key)
        if book is None:
            return False
        index = self.books.index(book)
        self.books.remove(book)
        if self.save():
            return True
        self.books.insert(index, book)  # put it back: the file still has it
        return False

    def replace(self, book: Book) -> bool:
        """Save an edited book. False leaves the old one in place."""
        existing = self.find(book.key)
        if existing is None:
            return False
        index = self.books.index(existing)
        self.books[index] = book
        if self.save():
            return True
        self.books[index] = existing
        return False
