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

"""The people and the loans, and the two files they live in."""

import logging
from pathlib import Path

from books.model import Book
from people.model import Loan, Person, now, open_loan_for
from shared.paths import loans_path, people_path
from shared.storage import DataFileDamaged, read_rows, write_rows

logger = logging.getLogger("katipcelebi")


def normalize_name(name: str) -> str:
    """A person's name with the stray spacing taken out."""
    return " ".join((name or "").split())


class Ledger:
    """Who you lend to, and what they have.

    People and loans are kept together because they are never asked about
    separately: every question about a person -- how many books they have, do
    they bring them back -- is a question about the loans.
    """

    def __init__(self, folder: Path):
        self.folder = Path(folder)
        self.people: list[Person] = []
        self.loans: list[Loan] = []
        self.rescued: list[Path] = []

    @property
    def people_path(self) -> Path:
        return people_path(self.folder)

    @property
    def loans_path(self) -> Path:
        return loans_path(self.folder)

    # ------------------------------------------------------------- loading ---
    def load(self) -> None:
        self.rescued = []
        self.people = self._read(self.people_path, Person)
        self.loans = self._read(self.loans_path, Loan)
        logger.info(
            "Loaded %d person/people, %d loan(s)",
            len(self.people),
            len(self.loans),
        )

    def _read(self, path: Path, kind) -> list:
        try:
            result = read_rows(path)
        except DataFileDamaged as damage:
            if damage.rescued_to is not None:
                self.rescued.append(damage.rescued_to)
            return []
        out = []
        for row in result.rows:
            try:
                out.append(kind.from_dict(row))
            except TypeError:
                logger.error("Skipping an unreadable entry in %s", path)
        return out

    # -------------------------------------------------------------- people ---
    def find_person(self, person_id: str) -> Person | None:
        return next((p for p in self.people if p.id == person_id), None)

    def person_named(self, name: str) -> Person | None:
        # Both sides normalized, not just the query: a name loaded from a hand-
        # edited people.json keeps whatever spacing was typed there, so "Ali
        # Veli" would not find a stored "Ali  Veli" and a second, identical-
        # looking person would be added beside the first.
        wanted = normalize_name(name).casefold()
        return next(
            (p for p in self.people if normalize_name(p.name).casefold() == wanted),
            None,
        )

    def add_person(self, name: str) -> Person | None:
        """Add somebody.

        None when the name is empty, already taken, or unsaved.
        """
        name = normalize_name(name)
        if not name or self.person_named(name) is not None:
            return None
        person = Person(id=Person.new_id(), name=name)
        self.people.append(person)
        if self._save_people():
            return person
        self.people.remove(person)
        return None

    def remove_person(self, person_id: str) -> bool:
        """Forget somebody. Their loans stay: they are what happened.

        A person still holding a book cannot be removed -- the history would
        then name somebody the app has never heard of.
        """
        person = self.find_person(person_id)
        if person is None or self.books_out_with(person_id):
            return False
        index = self.people.index(person)
        self.people.remove(person)
        if self._save_people():
            return True
        self.people.insert(index, person)
        return False

    # --------------------------------------------------------------- loans ---
    def can_lend(self, book: Book) -> bool:
        """Whether there is still a copy here to give.

        Owning three and having lent two means one is on the shelf. Only when
        every copy is out is there nothing to hand over.
        """
        return self.out_count(book.key) < book.copy_count

    def lend(self, book: Book, person: Person) -> bool:
        """Give a book to somebody. False changes nothing.

        A book with no copy left here cannot be lent: it is not here to give.
        """
        if not self.can_lend(book) or self.find_person(person.id) is None:
            return False
        loan = Loan(
            id=Loan.new_id(),
            book_key=book.key,
            book_title=book.title,
            person_id=person.id,
            person_name=person.name,
            lent_date=now(),
        )
        self.loans.append(loan)
        if self._save_loans():
            logger.info("Lent %s to %s", book.title, person.name)
            return True
        self.loans.remove(loan)
        return False

    def take_back(self, loan_id: str) -> bool:
        """Mark one loan as returned. False changes nothing.

        It takes the loan and not the book, because a book you own two of can
        be out with two people, and "give it back" would then have to guess
        which one came home.
        """
        loan = next((ln for ln in self.loans if ln.id == loan_id and ln.is_open), None)
        if loan is None:
            return False
        loan.return_date = now()
        if self._save_loans():
            logger.info("Got %s back from %s", loan.book_title, loan.person_name)
            return True
        loan.return_date = ""  # the file still says it is out; so do we
        return False

    # ----------------------------------------------------------- questions ---
    def open_loans_for(self, book_key: str) -> list[Loan]:
        from people.model import open_loans_for

        return open_loans_for(self.loans, book_key)

    def open_loan_for(self, book_key: str) -> Loan | None:
        return open_loan_for(self.loans, book_key)

    def out_count(self, book_key: str) -> int:
        return len(self.open_loans_for(book_key))

    def is_lent_out(self, book_key: str) -> bool:
        return bool(self.open_loans_for(book_key))

    def loans_of(self, person_id: str) -> list[Loan]:
        from people.model import loans_of

        return loans_of(self.loans, person_id)

    def books_out_with(self, person_id: str) -> list[Loan]:
        from people.model import books_out_with

        return books_out_with(self.loans, person_id)

    def trust_score(self, person_id: str) -> int:
        from people.model import trust_score

        return trust_score(self.loans, person_id)

    # -------------------------------------------------------------- saving ---
    def _save_people(self) -> bool:
        return write_rows(self.people_path, [p.to_dict() for p in self.people])

    def _save_loans(self) -> bool:
        return write_rows(self.loans_path, [loan.to_dict() for loan in self.loans])
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
