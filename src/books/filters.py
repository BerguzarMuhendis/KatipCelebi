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

"""Narrowing the library down, and putting it in order.

Deliberately free of Qt: what a filter *means* is worked out here and tested
here, and the widgets in grid.py only collect the answers.
"""

from dataclasses import dataclass

from books import tags
from books.model import Book, parse_rating, publish_year
from books.reading import STATUS_ANY, status_of
from shared.texts import text

SIGNED_ANY = "any"
SIGNED_YES = "yes"
SIGNED_NO = "no"

LENT_ANY = "any"
LENT_HOME = "home"
LENT_OUT = "out"

SORT_TITLE = "title"
SORT_RATING = "rating"
SORT_YEAR = "year"

# What the search box looks in. "All" is the everyday one; the rest are for
# when a word means different things in different places -- an author called
# Penguin, a book called Penguin, and Penguin the publisher.
SEARCH_ALL = "all"
SEARCH_TITLE = "title"
SEARCH_AUTHORS = "authors"
SEARCH_ISBN = "isbn"
SEARCH_PUBLISHERS = "publishers"
SEARCH_FIELDS = (
    SEARCH_ALL,
    SEARCH_TITLE,
    SEARCH_AUTHORS,
    SEARCH_ISBN,
    SEARCH_PUBLISHERS,
)

# What a ticked "signed" box writes. Stored as text, like every other field.
SIGNED_VALUE = "yes"
# Read generously: the library is a JSON file people do open and edit, and
# somebody typing "true" there plainly means the same as our "yes".
_MEANS_YES = {"yes", "true", "1", "evet"}


def is_signed(book: Book) -> bool:
    return book.signed.strip().lower() in _MEANS_YES


def haystack(book: Book, field: str, lent_out: bool = False) -> str:
    """The text one search looks through, folded for comparing.

    Searching everything is not the same as searching each field and joining
    the answers: "signed" and "lent out" are things you can type, and they are
    not written in the book anywhere.
    """
    if field == SEARCH_TITLE:
        parts = [book.title]
    elif field == SEARCH_AUTHORS:
        parts = [book.authors]
    elif field == SEARCH_ISBN:
        parts = [book.display_isbn, book.isbn_10, book.isbn_13]
    elif field == SEARCH_PUBLISHERS:
        parts = [book.publishers]
    else:
        parts = [
            book.authors,
            book.title,
            book.display_isbn,
            book.publishers,
            book.series,
            # As they read, not as they are stored: somebody searching for
            # "Science fiction" is typing what the card shows them.
            tags.show(book.tags),
            text("status_" + status_of(book)),
        ]
        if is_signed(book):
            # So typing "signed" finds them. One word only -- see the note on
            # signed_search_word in texts.py.
            parts.append(text("signed_search_word"))
        if lent_out:
            parts.append(text("lent_search_word"))
    return " ".join(part.casefold() for part in parts if part)


@dataclass(frozen=True)
class Filters:
    """What the user has narrowed the library down to."""

    query: str = ""
    search_field: str = SEARCH_ALL
    min_rating: int = 0
    signed: str = SIGNED_ANY
    lent: str = LENT_ANY
    status: str = STATUS_ANY
    tag: str = ""

    def allows(self, book: Book, lent_out: bool = False) -> bool:
        """Whether this book survives.

        ``lent_out`` is whether any copy is with somebody -- the ledger knows
        that and the book does not, so it is handed in.
        """
        wanted = self.query.strip().casefold()
        if wanted and wanted not in haystack(book, self.search_field, lent_out):
            return False
        if self.min_rating and parse_rating(book.rating) < self.min_rating:
            return False
        if self.signed == SIGNED_YES and not is_signed(book):
            return False
        if self.signed == SIGNED_NO and is_signed(book):
            return False
        # A book you own three of, one of them out, is a book that is lent out.
        # Owning a spare does not make it not-lent: somebody still has one.
        if self.lent == LENT_OUT and not lent_out:
            return False
        if self.lent == LENT_HOME and lent_out:
            return False
        if self.status != STATUS_ANY and status_of(book) != self.status:
            return False
        return not (self.tag and not tags.contains(book.tags, self.tag))


def sort_key(book: Book, mode: str):
    """How to order one book.

    Every key is a tuple ending in the title, so books that tie -- and with
    ratings out of five, most of them tie -- come out alphabetically rather
    than in whatever order the file happened to hold them.
    """
    title = book.title.casefold()
    if mode == SORT_RATING:
        return (-parse_rating(book.rating), title)
    if mode == SORT_YEAR:
        return (-publish_year(book.publish_date), title)
    return (title,)


def arrange(books: list[Book], mode: str, descending: bool = False) -> list[Book]:
    """The books in the order to show them."""
    ordered = sorted(books, key=lambda b: sort_key(b, mode))
    return list(reversed(ordered)) if descending else ordered
