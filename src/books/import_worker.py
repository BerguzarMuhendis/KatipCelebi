# Worker tasks for looking up, importing, and submitting books.
import logging
import time

from PyQt6.QtCore import QObject, QRunnable, pyqtSignal

from books.openlibrary import SUBMIT_FAILED, fetch_book, submit_book

logger = logging.getLogger("katipcelebi")


class LookupSignals(QObject):
    done = pyqtSignal(object, str)  # Book | None, the ISBN it was asked about


class LookupTask(QRunnable):
    """Ask Open Library about one ISBN, off the main thread."""

    def __init__(self, isbn: str, signals: LookupSignals):
        super().__init__()
        self.isbn = isbn
        self.signals = signals

    def run(self):
        try:
            book = fetch_book(self.isbn)
        except Exception:
            logger.exception("Lookup failed for %s", self.isbn)
            book = None
        self.signals.done.emit(book, self.isbn)


class ImportSignals(QObject):
    done = pyqtSignal(list, list, bool)  # the books found, the ISBNs that were not, network_problem


class ImportTask(QRunnable):
    """Look a whole list of ISBNs up, off the main thread."""

    def __init__(self, isbns: list, signals: ImportSignals):
        super().__init__()
        self.isbns = isbns
        self.signals = signals

    def run(self):
        found, missing = [], []
        consecutive_failures = 0
        network_problem = False
        for isbn in self.isbns:
            try:
                book = fetch_book(isbn)
            except Exception:
                logger.exception("Lookup failed for %s during an import", isbn)
                book = None
            if book is None or not book.title:
                missing.append(isbn)
                consecutive_failures += 1
            else:
                found.append(book)
                consecutive_failures = 0

            # Throttle to be polite and avoid rate limiting.
            time.sleep(0.2)

            if consecutive_failures >= 3:
                network_problem = True
                logger.warning("Import aborted after repeated lookup failures")
                break
        self.signals.done.emit(found, missing, network_problem)


class SubmitSignals(QObject):
    done = pyqtSignal(str)  # a submit reason: "" for success


class SubmitTask(QRunnable):
    """Offer one book to Open Library, off the main thread."""

    def __init__(self, book, username, password, signals: SubmitSignals):
        super().__init__()
        self.book = book
        self.username = username
        self.password = password
        self.signals = signals

    def run(self):
        try:
            reason = submit_book(self.book, self.username, self.password)
        except Exception:
            logger.exception("Submitting %s to Open Library", self.book.key)
            reason = SUBMIT_FAILED
        self.signals.done.emit(reason)
