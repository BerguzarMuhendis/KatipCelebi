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

"""People you lend to, and the loans themselves.

Every loan the library has ever made lives in one list. Nothing else records
who has a book: "is this book out?" and "how far can I trust this person?" are
questions *answered* from that list, never stored alongside it. Two places
holding the same fact is two places that can disagree, and the one that is
wrong is always the one being read.
"""

import secrets
import string
from dataclasses import asdict, dataclass, fields
from datetime import datetime
from typing import Any


def normalize_id(value: str | None) -> str:
    """IDs are shown and compared in uppercase so the UI stays consistent."""
    text = (value or "").upper().strip()
    if len(text) == 9 and text[4] == "-":
        return text
    parts = [part for part in text.replace("-", "") if part.isalnum()]
    if len(parts) >= 8:
        return f"{''.join(parts[:4])}-{''.join(parts[4:8])}"
    return text


def now() -> str:
    """The moment, as it is written down."""
    # Wall-clock time, deliberately naive -- the stamp is a local record.
    return datetime.now().isoformat(timespec="seconds")  # noqa: DTZ005


def as_date(stamp: str) -> str:
    """A stamp as the day it names -- what a person wants to read."""
    return (stamp or "")[:10]


@dataclass
class Person:
    """Somebody you lend books to.

    Nothing but a name and an id. How many books they have borrowed and whether
    they bring them back is in the loans, and is worked out when asked.
    """

    id: str = ""
    name: str = ""

    @staticmethod
    def new_id() -> str:
        alphabet = string.ascii_uppercase + string.digits
        left = "".join(secrets.choice(alphabet) for _ in range(4))
        right = "".join(secrets.choice(alphabet) for _ in range(4))
        return normalize_id(f"{left}-{right}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "Person":
        if not isinstance(data, dict):
            raise TypeError(
                f"a person must be a JSON object, got {type(data).__name__}"
            )
        known = {f.name for f in fields(cls)}
        values = {
            k: ("" if v is None else str(v)) for k, v in data.items() if k in known
        }
        if "id" in values:
            values["id"] = normalize_id(values["id"])
        return cls(**values)


@dataclass
class Loan:
    """One book, in somebody's hands, from one day to another.

    `book_title` is written down as it was at the time rather than looked up:
    the history has to still read properly after the book itself is deleted.
    """

    id: str = ""
    book_key: str = ""
    book_title: str = ""
    person_id: str = ""
    person_name: str = ""
    lent_date: str = ""
    return_date: str = ""

    @staticmethod
    def new_id() -> str:
        alphabet = string.ascii_uppercase + string.digits
        left = "".join(secrets.choice(alphabet) for _ in range(4))
        right = "".join(secrets.choice(alphabet) for _ in range(4))
        return normalize_id(f"{left}-{right}")

    @property
    def is_open(self) -> bool:
        """Whether the book is still out."""
        return not self.return_date.strip()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Any) -> "Loan":
        if not isinstance(data, dict):
            raise TypeError(f"a loan must be a JSON object, got {type(data).__name__}")
        known = {f.name for f in fields(cls)}
        values = {
            k: ("" if v is None else str(v)) for k, v in data.items() if k in known
        }
        if "id" in values:
            values["id"] = normalize_id(values["id"])
        return cls(**values)


# --------------------------------------------------------------- questions ---
# All of these read the list of loans. None of them writes anything down.


def open_loans_for(loans: list[Loan], book_key: str) -> list[Loan]:
    """Every copy of this book that is out right now, oldest first.

    A book you own two of can be in two people's hands at once, so this is a
    list and not a single loan. It is empty for a book that is all here.
    """
    return [loan for loan in loans if loan.book_key == book_key and loan.is_open]


def open_loan_for(loans: list[Loan], book_key: str) -> Loan | None:
    """Who has this book right now, if anyone -- the longest-standing of them.

    Only for the places that can say one name and no more. Anything that has to
    be right about a book with several copies out wants open_loans_for.
    """
    out = open_loans_for(loans, book_key)
    return out[0] if out else None


def out_count(loans: list[Loan], book_key: str) -> int:
    """How many copies of this book are in somebody else's hands."""
    return len(open_loans_for(loans, book_key))


def is_lent_out(loans: list[Loan], book_key: str) -> bool:
    """Whether any copy is out.

    Says nothing about whether one is still here.
    """
    return bool(open_loans_for(loans, book_key))


def loans_of(loans: list[Loan], person_id: str) -> list[Loan]:
    """Everything this person has ever borrowed, newest last."""
    return [loan for loan in loans if loan.person_id == person_id]


def books_out_with(loans: list[Loan], person_id: str) -> list[Loan]:
    return [loan for loan in loans_of(loans, person_id) if loan.is_open]


def returned_count(loans: list[Loan], person_id: str) -> int:
    return len([loan for loan in loans_of(loans, person_id) if not loan.is_open])


def trust_score(loans: list[Loan], person_id: str) -> int:
    """How well this person gives books back.

    One point per book returned, one off for each still out. Worked out from
    the history every time it is asked for, so it cannot drift away from what
    actually happened -- and correcting the history corrects the score.
    """
    return returned_count(loans, person_id) - len(books_out_with(loans, person_id))
