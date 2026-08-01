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

"""Asking Open Library about a book.

Open Library is a wiki: anyone can edit any record, and the schema is a
suggestion. A field documented as a list of strings may hold a null, a number,
a {'value': ...} wrapper, or a bare string. So nothing here trusts the shape of
what comes back -- every field is read on its own, and an odd one costs that
field rather than the book.
"""

import json
import logging
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from books import tags
from books.model import Book, normalize_isbn
from shared.paths import cover_cache_dir

logger = logging.getLogger("katipcelebi")

# Open Library asks that tools identify themselves, so a misbehaving client can
# be told apart from the rest.
USER_AGENT = "KatipCelebi/2.0 (+https://github.com/farukylmz0550/KatipCelebi)"
API_ROOT = "https://openlibrary.org"
COVERS_ROOT = "https://covers.openlibrary.org/b/isbn/"
TIMEOUT = 10

COVER_SIZE_THUMB = "M"
COVER_SIZE_LARGE = "L"

LANGUAGES = {
    "/languages/eng": "English",
    "/languages/tur": "Turkish",
    "/languages/fra": "French",
    "/languages/deu": "German",
    "/languages/spa": "Spanish",
    "/languages/ita": "Italian",
    "/languages/rus": "Russian",
    "/languages/zho": "Chinese",
    "/languages/jpn": "Japanese",
    "/languages/ara": "Arabic",
}


# --------------------------------------------------------- reading a reply ---
def _get_json(url: str) -> Any:
    """Fetch and parse JSON. None for anything that did not work.

    Every failure is the same failure from here: no answer. A body that is not
    UTF-8 at all is a proxy's error page, which is a network problem, not a
    missing book.
    """
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        json.JSONDecodeError,
        UnicodeDecodeError,
        OSError,
        TimeoutError,
    ):
        logger.debug("Open Library request failed: %s", url, exc_info=True)
        return None


def _text(value: Any) -> str:
    """Any field, as the string to show.

    Open Library writes some fields plainly, some as {'value': ...}, some as
    lists of either. All three mean the same thing to a reader.
    """
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return str(value.get("value", "")).strip()
    if isinstance(value, list):
        return ", ".join(
            part for part in (_text(item) for item in value) if part
        )
    return ""


def _string_list(value: Any) -> list[str]:
    """A field documented as a list of strings, as exactly that.

    Refused rather than iterated when it isn't a list: a bare string would be
    walked letter by letter, and the book's ISBN would be saved as
    "9, 7, 8, 0, 3...". A null inside the list would raise on join -- and an
    exception in a worker thread is what PyQt turns into an abort.
    """
    if not isinstance(value, list):
        return []
    return [
        item.strip()
        for item in value
        if isinstance(item, str) and item.strip()
    ]


def _dict_list(value: Any) -> list[dict]:
    """A field documented as a list of objects, as exactly that."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


# --------------------------------------------------------------- the book ---
def _author_name(key: str) -> str:
    data = _get_json(f"{API_ROOT}{key}.json")
    return _text(data.get("name")) if isinstance(data, dict) else ""


def _work_subjects(work_key: str) -> list[str]:
    if not work_key:
        return []
    data = _get_json(f"{API_ROOT}{work_key}.json")
    return _string_list(data.get("subjects")) if isinstance(data, dict) else []


def fetch_book(isbn: str) -> Book | None:
    """Everything an ISBN lookup can tell us.

    None when there is no such book.
    """
    key = normalize_isbn(isbn)
    edition = _get_json(f"{API_ROOT}/isbn/{key}.json")
    if not isinstance(edition, dict):
        return None

    book = Book(key=key)
    book.title = _text(edition.get("title"))
    book.subtitle = _text(edition.get("subtitle"))
    book.publish_date = _text(edition.get("publish_date"))
    book.publishers = _text(edition.get("publishers"))
    book.publish_places = _text(edition.get("publish_places"))
    book.edition_name = _text(edition.get("edition_name"))
    book.series = _text(edition.get("series"))
    book.number_of_pages = _text(edition.get("number_of_pages"))
    book.isbn_10 = ", ".join(_string_list(edition.get("isbn_10")))
    book.isbn_13 = ", ".join(_string_list(edition.get("isbn_13")))

    names = [
        _author_name(a["key"])
        for a in _dict_list(edition.get("authors"))
        if a.get("key")
    ]
    book.authors = ", ".join(name for name in names if name)

    spoken = []
    for entry in _dict_list(edition.get("languages")):
        code = str(entry.get("key", ""))
        spoken.append(LANGUAGES.get(code, code.replace("/languages/", "")))
    book.languages = ", ".join(name for name in spoken if name)

    # The edition often has no subjects; the work behind it usually does.
    subjects = _string_list(edition.get("subjects"))
    if not subjects:
        works = _dict_list(edition.get("works"))
        if works:
            subjects = _work_subjects(str(works[0].get("key", "")))
    book.subjects = ", ".join(subjects[:15])
    # Worked out here, where the subjects are still a list. Once they are
    # joined into the line above, a subject with a comma in it ("Lee, Harper -
    # Prose & Criticism") is indistinguishable from two subjects.
    book.tags = tags.from_subjects(subjects[:15])

    return book


# -------------------------------------------------------------- the cover ---
# The first bytes of the formats Open Library serves covers in.
_IMAGE_MAGIC = (
    b"\xff\xd8\xff",
    b"\x89PNG\r\n\x1a\n",
    b"GIF87a",
    b"GIF89a",
    b"RIFF",
)


# ---------------------------------------------------- giving one back ---
# Why a submission did not go through, for the page to turn into a sentence.
# An empty string is success.
SUBMIT_OK = ""
SUBMIT_LOGIN = "login"
SUBMIT_DENIED = "denied"
SUBMIT_NETWORK = "network"
SUBMIT_FAILED = "failed"


def _edition(book: Book) -> dict:
    """A book as Open Library's import endpoint wants it.

    Only the fields we actually have. source_records is required, and names the
    book as one a person entered by hand rather than a scan or a MARC record.
    """
    isbn = normalize_isbn(book.key)
    edition = {
        "title": book.title,
        "source_records": [f"katipcelebi-manual:{isbn}"],
    }
    if book.authors.strip():
        edition["authors"] = [
            {"name": name.strip()}
            for name in book.authors.split(",")
            if name.strip()
        ]
    if book.publishers.strip():
        edition["publishers"] = [
            p.strip() for p in book.publishers.split(",") if p.strip()
        ]
    if book.publish_date.strip():
        edition["publish_date"] = book.publish_date.strip()
    if book.number_of_pages.strip():
        edition["number_of_pages"] = book.number_of_pages.strip()
    if len(isbn) == 13:
        edition["isbn_13"] = [isbn]
    elif len(isbn) == 10:
        edition["isbn_10"] = [isbn]
    return edition


def _post(opener, url: str, payload: dict):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
        method="POST",
    )
    return opener.open(request, timeout=TIMEOUT)


def submit_book(book: Book, username: str, password: str) -> str:
    """Offer a book to Open Library. Empty string on success, else a reason.

    Best effort, and never fatal: the /api/import endpoint is open only to
    accounts with import permission, so an ordinary account gets a 403 and the
    book simply stays in the local library. The whole point is contributing a
    book the catalogue did not have -- failing to is no worse than not trying.
    """
    import http.cookiejar

    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar)
    )

    try:
        _post(
            opener,
            f"{API_ROOT}/account/login",
            {"username": username, "password": password},
        ).close()
    except urllib.error.HTTPError:
        logger.warning("Open Library login refused for %s", username)
        return SUBMIT_LOGIN
    except (urllib.error.URLError, OSError, TimeoutError):
        logger.warning("Open Library login could not be reached")
        return SUBMIT_NETWORK

    try:
        reply = _post(opener, f"{API_ROOT}/api/import", _edition(book))
        with reply:
            if reply.status in (200, 201):
                logger.info("Submitted %s to Open Library", book.key)
                return SUBMIT_OK
        logger.warning("Open Library import returned %s", reply.status)
        return SUBMIT_FAILED
    except urllib.error.HTTPError as error:
        # 403 is the everyday one: the account cannot import. Told apart from
        # a real failure so the user is not sent chasing a fault of their own.
        reason = SUBMIT_DENIED if error.code == 403 else SUBMIT_FAILED
        logger.warning("Open Library import failed (HTTP %s)", error.code)
        return reason
    except (urllib.error.URLError, OSError, TimeoutError):
        logger.warning("Open Library import could not be reached")
        return SUBMIT_NETWORK


def _is_image(data: bytes) -> bool:
    return bool(data) and data.startswith(_IMAGE_MAGIC)


def cover_cache_path(isbn: str, size: str) -> Path:
    return cover_cache_dir() / (f"{normalize_isbn(isbn)}_{size}.jpg")


def fetch_cover(isbn: str, size: str = COVER_SIZE_THUMB) -> bytes | None:
    """A book's cover, from the cache when we have it.

    None when there isn't one.
    """
    key = normalize_isbn(isbn)
    if not key:
        return None

    cached = cover_cache_path(key, size)
    if cached.exists():
        try:
            data = cached.read_bytes()
            if data:
                return data
        except OSError:
            logger.debug(
                "Could not read the cached cover %s", cached, exc_info=True
            )

    url = f"{COVERS_ROOT}{key}-{size}.jpg?default=false"
    try:
        request = urllib.request.Request(
            url, headers={"User-Agent": USER_AGENT}
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT) as reply:
            data = reply.read()
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        OSError,
        TimeoutError,
    ):
        logger.debug("No cover for %s (%s)", key, size, exc_info=True)
        return None

    if not _is_image(data):
        # A 200 that isn't a picture: a captive portal, a rate-limit notice.
        # Caching it would break that book's cover for good, because the cache
        # hit means the real one is never asked for again.
        logger.debug(
            "The cover reply for %s is not an image; not caching it", key
        )
        return None

    try:
        cached.write_bytes(data)
    except OSError:
        logger.debug("Could not cache the cover %s", cached, exc_info=True)
    return data
