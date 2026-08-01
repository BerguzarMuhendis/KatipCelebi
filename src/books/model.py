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

"""What a book is.

No Qt, no files, no network -- just the record and its rules.
"""

import re
import uuid
from dataclasses import asdict, dataclass, fields
from typing import Any

# A book with no ISBN still needs a name of its own to be found by. Nothing is
# ever shown to the user under this key -- see Book.display_isbn.
LOCAL_KEY_PREFIX = "local_"

# Somebody owning more than this many of one book is somebody who has mistyped.
# The ceiling is here so a stray keystroke cannot ask the lending panel to draw
# thousands of rows.
MAX_COPIES = 999


@dataclass
class Book:
    """One book on the shelf.

    Every field is a string, because that is what the form widgets hand over
    and what the file holds; the type annotations are here so a typo in a field
    name is an error rather than a silent empty string.

    `key` identifies the book everywhere: the grid keys its cards by it and the
    detail window finds the book again with it. It is the ISBN when there is
    one, and a generated `local_...` when there is not -- never blank, or two
    ISBN-less books would be the same book.
    """

    key: str = ""
    title: str = ""
    subtitle: str = ""
    authors: str = ""
    publishers: str = ""
    publish_date: str = ""
    publish_places: str = ""
    edition_name: str = ""
    series: str = ""
    number_of_pages: str = ""
    languages: str = ""
    isbn_10: str = ""
    isbn_13: str = ""
    subjects: str = ""
    rating: str = ""
    notes: str = ""
    status: str = ""
    tags: str = ""
    started_date: str = ""
    finished_date: str = ""
    signed: str = ""
    copies: str = ""

    # -------------------------------------------------------------- copies ---
    @property
    def copy_count(self) -> int:
        """How many of this book are on the shelf. Never less than one.

        Empty means one: every book written before there was a copies field has
        one, and so does every book somebody adds without thinking about it.
        """
        return parse_copies(self.copies)

    # ---------------------------------------------------------------- keys ---
    @staticmethod
    def new_local_key() -> str:
        """A key for a book that has no ISBN."""
        return LOCAL_KEY_PREFIX + uuid.uuid4().hex[:12]

    @property
    def is_local_key(self) -> bool:
        return self.key.startswith(LOCAL_KEY_PREFIX)

    @property
    def display_isbn(self) -> str:
        """The ISBN to show. Empty for a book that hasn't got one.

        A generated key is our bookkeeping, not a fact about the book, and
        showing it would be telling the user something untrue.
        """
        return "" if self.is_local_key else self.key

    # ------------------------------------------------------------ the file ---
    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def field_names(cls) -> list[str]:
        return [f.name for f in fields(cls)]

    @classmethod
    def from_dict(cls, data: Any) -> "Book":
        """Build a book from one entry in the file.

        The file is JSON a person can open and edit, so nothing in it is
        promised: a number where text belongs, a null, a missing field, an
        extra one. Anything unusable becomes the empty string rather than an
        exception -- a book with an odd rating is still the user's book.
        """
        if not isinstance(data, dict):
            raise TypeError(
                f"a book must be a JSON object, got {type(data).__name__}"
            )
        known = set(cls.field_names())
        values = {}
        for name, raw in data.items():
            if name in known:
                values[name] = "" if raw is None else str(raw)
        return cls(**values)


def parse_rating(value: str) -> int:
    """A stored rating as a number of stars. Anything odd is no stars.

    The file can be edited by hand, so "5", "3.0", "" and "banana" all have to
    mean something here rather than raise.
    """
    try:
        return max(0, min(5, int(float(str(value).strip()))))
    except (TypeError, ValueError):
        return 0


def parse_copies(value: str) -> int:
    """A stored copy count as a number. Anything odd is one.

    A book in the library is at least one book -- that is what having it means.
    So "", "0", "-3" and "banana" all mean one, and only a real count above one
    means more.
    """
    try:
        return max(1, min(MAX_COPIES, int(float(str(value).strip()))))
    except (TypeError, ValueError):
        return 1


def normalize_isbn(text: str) -> str:
    """An ISBN with the dashes and spaces people type in it taken out."""
    return re.sub(r"[^0-9Xx]", "", text or "").upper()


def is_valid_isbn10(isbn: str) -> bool:
    isbn = normalize_isbn(isbn)
    if len(isbn) != 10:
        return False
    total = 0
    for i, char in enumerate(isbn):
        if char == "X":
            # Only the check digit may be X: it is how 10 is written in one
            # place.
            if i != 9:
                return False
            value = 10
        elif char.isdigit():
            value = int(char)
        else:
            return False
        total += value * (10 - i)
    return total % 11 == 0


def is_valid_isbn13(isbn: str) -> bool:
    isbn = normalize_isbn(isbn)
    if len(isbn) != 13 or not isbn.isdigit():
        return False
    total = sum(
        int(char) * (1 if i % 2 == 0 else 3) for i, char in enumerate(isbn)
    )
    return total % 10 == 0


def is_valid_isbn(isbn: str) -> bool:
    return is_valid_isbn10(isbn) or is_valid_isbn13(isbn)


# What is wrong with an ISBN, when something is. The caller turns these into
# a sentence; the rule itself has no business knowing the words.
ISBN_OK = "ok"
ISBN_EMPTY = "empty"
ISBN_LENGTH = "length"
ISBN_CHECKSUM_10 = "checksum10"
ISBN_CHECKSUM_13 = "checksum13"


def check_isbn(typed: str) -> tuple:
    """What is wrong with this ISBN, and how many digits it has.

    One "that is not an ISBN" for every case tells somebody who typed twelve
    digits to go and count them themselves. The check digit exists precisely
    to catch a typo, so when it is the check digit that failed, say so.
    """
    isbn = normalize_isbn(typed)
    if not isbn:
        return (ISBN_EMPTY, 0)
    if len(isbn) == 10:
        return (ISBN_OK if is_valid_isbn10(isbn) else ISBN_CHECKSUM_10, 10)
    if len(isbn) == 13:
        return (ISBN_OK if is_valid_isbn13(isbn) else ISBN_CHECKSUM_13, 13)
    return (ISBN_LENGTH, len(isbn))


def publish_year(publish_date: str) -> int:
    """The year in a publish date, or 0. Open Library writes these freehand.

    The lookarounds rather than \\b: "5 March 1981" must not read as 5198, and
    \\b on the left would miss "c1999", where the c and the 1 are both word
    characters.
    """
    match = re.search(r"(?<!\d)(\d{4})(?!\d)", str(publish_date or ""))
    return int(match.group(1)) if match else 0
