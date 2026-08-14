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

"""Tags: what a book is about.

A tag is stored folded to lower case and shown with a capital, so "Science
fiction", "science fiction" and "SCIENCE FICTION" are one tag rather than
three. Nothing is translated here -- the app speaks one language today -- but
storing a settled form is what makes translating possible later without going
back over everybody's library.

The other half of this file is about Open Library. Its `subjects` list mixes
two different things: what a book is about, and how a shop or a cataloguer
files it. Only the first kind is a tag worth having.
"""

import re

# How many of Open Library's subjects to take. They run from the defining to
# the incidental, and all fifteen would bury the useful ones.
MAX_SUBJECT_TAGS = 6

# Somewhere to start. A new library has no tags of its own, and an empty box
# with a placeholder in it does not tell anybody what a tag is meant to be.
#
# Open Library's own wording, because that is what a looked-up book arrives
# tagged with -- pick "science fiction" here and it matches the ones that came
# from the catalogue, rather than sitting beside them as a near-miss.
STARTER_TAGS = (
    "fiction",
    "short stories",
    "poetry",
    "history",
    "biography",
    "philosophy",
    "science",
    "science fiction",
    "fantasy",
    "detective and mystery stories",
    "juvenile fiction",
    "textbooks",
    "reference",
    "religion",
    "art",
    "travel",
)

# Every pattern below was taken from real Open Library answers, not imagined:
#
# "Fiction / Literary", "Literature - Classics / Criticism"   shelving paths
# "Lee, Harper - Prose & Criticism"                           filed by author
# "Literature: Classics"                                      shelving "English
# Translations", "Translations into Yiddish"         about the edition "German
# language"                                           about the edition
# "British and Irish fiction (fictional works by one author)"  cataloguer's
# note "Accessible book", "Reading Group Guide", "nyt:paperback=…"  not about
# the book
_NOISE_MARKERS = (" / ", "/", ":", " - ")
_NOISE_WORDS = (
    "translations",
    "fictional works",
    "accessible book",
    "protected daisy",
    "in library",
    "overdrive",
    "large type",
    "reading group guide",
    "staff picks",
    "open_syllabus_project",
)
# The languages a book might be *printed* in, as Open Library names them.
_LANGUAGE_NAMES = (
    "english",
    "turkish",
    "french",
    "german",
    "spanish",
    "italian",
    "russian",
    "chinese",
    "japanese",
    "arabic",
    "dutch",
    "portuguese",
    "yiddish",
    "indonesian",
)
# A bare year or year range: "1616", "1939-1945".
_YEAR_ONLY = re.compile(r"^\d{3,4}\s*[-–]?\s*\d{0,4}$")


# ------------------------------------------------------------ tags as tags ---
def split_tags(value: str) -> list[str]:
    """A tags field as the tags in it."""
    return [tag.strip() for tag in (value or "").split(",") if tag.strip()]


def canonical(tag: str) -> str:
    """The form a tag is stored in.

    Folded, so one idea is one tag however it was typed. A comma is taken out
    rather than kept: the field is comma-separated, so a tag simply cannot
    contain one -- and letting it through would silently turn one tag into two
    the next time the field was read.
    """
    return " ".join(tag.replace(",", " ").split()).lower()


def display(tag: str) -> str:
    """A tag as it is shown: "science fiction" reads as "Science fiction"."""
    tag = tag.strip()
    return tag[:1].upper() + tag[1:] if tag else ""


def store(value: str) -> str:
    """A tags field as typed, ready for the file. Deduplicated, order kept."""
    seen, out = set(), []
    for tag in split_tags(value):
        settled = canonical(tag)
        if settled and settled not in seen:
            seen.add(settled)
            out.append(settled)
    return ", ".join(out)


def show(value: str) -> str:
    """A stored tags field as the text to put in front of somebody."""
    return ", ".join(display(tag) for tag in split_tags(value))


def contains(value: str, wanted: str) -> bool:
    """Whether a tags field holds a given tag, however either was cased.

    The stored field is canonical already, but the library is a JSON file
    people do open and edit, and one who types "Science Fiction" by hand means
    the tag the filter offers as "science fiction". Fold both sides so the
    filter still finds their book.
    """
    target = canonical(wanted)
    return any(canonical(tag) == target for tag in split_tags(value))


def tags_in_use(books) -> list[str]:
    """Every distinct tag across the library, in alphabetical order."""
    seen = set()
    for book in books:
        seen.update(split_tags(book.tags))
    return sorted(seen)


def suggestions(books) -> list[str]:
    """What to offer somebody typing a tag: theirs first, then a start.

    Their own tags lead, because a library that already says "sea stories"
    wants that again and not a near-miss beside it. The starters follow, and
    only the ones they are not already using -- an offer to add a tag they
    have is an offer that does nothing.
    """
    mine = tags_in_use(books)
    have = set(mine)
    return mine + [tag for tag in STARTER_TAGS if tag not in have]


# ------------------------------------------------- Open Library's subjects ---
def _is_edition_language(lowered: str) -> bool:
    """ "German language" -- which edition this is, not what it is about.

    Matched against real language names rather than a bare " language" suffix:
    that also threw away "Sign language" and "Body language", which are
    subjects in their own right.
    """
    return any(lowered == f"{name} language" for name in _LANGUAGE_NAMES)


def is_noise(subject: str) -> bool:
    """Whether a subject describes the catalogue entry rather than the book."""
    lowered = subject.lower()
    if any(marker in subject for marker in _NOISE_MARKERS):
        return True
    if any(word in lowered for word in _NOISE_WORDS):
        return True
    # "Fiction in Spanish" is the printing; "Portuguese Fiction" is the
    # writing, and is left alone.
    return _is_edition_language(lowered) or lowered.startswith("fiction in ")


def _heading(subject: str) -> str:
    """The part of a subject that names the topic.

    Library subjects qualify a heading with subdivisions after "--", and the
    heading is the half that says what the book is about: "Traffic accidents --
    Fiction" is a novel about traffic accidents, and "-- Fiction" only repeats
    what the shelf already knows.
    """
    return subject.split("--")[0].strip() if "--" in subject else subject.strip()


def _clean(subject: str) -> str:
    """One subject as a tag: no trailing punctuation, no parenthetical."""
    value = re.sub(r"\([^)]*\)", "", subject or "").strip(" .,;")
    return re.sub(r"\s+", " ", value)


def _terms(heading: str) -> list[str]:
    """The comma-separated terms in one subject heading.

    A comma means two different things in this field. "Fiction, Romance,
    Historical, Regency" is a list of four topics. "Shakespeare, William,
    1564-1616" and "World War, 1939-1945" are single headings, written surname-
    first or qualified by a date -- splitting those filed books under "William"
    and "1564-1616". The date is the tell: where one is present, the heading
    names one thing, and only its first part says what.
    """
    pieces = [piece.strip() for piece in heading.split(",")]
    if any(_YEAR_ONLY.match(piece) for piece in pieces if piece):
        return pieces[:1]
    return pieces


def from_subjects(subjects: list[str]) -> str:
    """Open Library's subject list, as a tags field to store.

    Takes the list, never a comma-joined string of it: Open Library has single
    subjects with commas inside ("Lee, Harper - Prose & Criticism"), and
    splitting on the comma would file the book under "Lee".
    """
    seen, out = set(), []
    for raw in subjects or []:
        if not isinstance(raw, str):
            continue
        heading = _heading(raw)
        if is_noise(heading):
            continue
        for piece in _terms(heading):
            subject = _clean(piece)
            if not subject or is_noise(subject):
                continue
            tag = canonical(subject)
            if tag and tag not in seen:
                seen.add(tag)
                out.append(tag)
            if len(out) >= MAX_SUBJECT_TAGS:
                return ", ".join(out)
    return ", ".join(out)
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
