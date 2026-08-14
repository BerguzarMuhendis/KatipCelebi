import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from books import tags
from books.model import Book, normalize_isbn
from .client import API_ROOT, _get_json

logger = logging.getLogger("katipcelebi")

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


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        return str(value.get("value", "")).strip()
    if isinstance(value, list):
        return ", ".join(part for part in (_text(item) for item in value) if part)
    return ""


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _dict_list(value: Any) -> list[dict]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _author_name(key: str) -> str:
    data = _get_json(f"{API_ROOT}{key}.json")
    return _text(data.get("name")) if isinstance(data, dict) else ""


def _work_subjects(work_key: str) -> list[str]:
    if not work_key:
        return []
    data = _get_json(f"{API_ROOT}{work_key}.json")
    return _string_list(data.get("subjects")) if isinstance(data, dict) else []


def fetch_book(isbn: str) -> Book | None:
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

    author_keys = [a.get("key") for a in _dict_list(edition.get("authors")) if a.get("key")]
    names = []
    if author_keys:
        max_workers = min(8, len(author_keys))
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_author_name, k): k for k in author_keys}
            for fut in as_completed(futures):
                try:
                    n = fut.result()
                except Exception:
                    n = ""
                if n:
                    names.append(n)
    book.authors = ", ".join(name for name in names if name)

    spoken = []
    for entry in _dict_list(edition.get("languages")):
        code = str(entry.get("key", ""))
        spoken.append(LANGUAGES.get(code, code.replace("/languages/", "")))
    book.languages = ", ".join(name for name in spoken if name)

    subjects = _string_list(edition.get("subjects"))
    if not subjects:
        works = _dict_list(edition.get("works"))
        if works:
            subjects = _work_subjects(str(works[0].get("key", "")))
    book.subjects = ", ".join(subjects[:15])
    book.tags = tags.from_subjects(subjects[:15])

    return book
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
