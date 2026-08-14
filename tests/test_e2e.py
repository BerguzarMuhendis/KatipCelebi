from pathlib import Path
import tempfile

from books.model import Book
from books import excel_io


def test_export_library_creates_file(tmp_path: Path):
    out = tmp_path / "export.xlsx"
    b = Book()
    b.key = "9780306406157"
    b.title = "Test Book"
    b.authors = "A. Author"
    books = [b]

    # ledger can be None; export_library should still succeed (writes file)
    ok = excel_io.export_library(books, ledger=None, path=out)
    assert ok
    assert out.exists()

    # basic sanity: file is non-empty
    assert out.stat().st_size > 100
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
