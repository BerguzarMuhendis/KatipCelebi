from books.model import normalize_isbn, is_valid_isbn, is_valid_isbn10, is_valid_isbn13


def test_normalize_and_validate_isbn10():
    raw = "0-306-40615-2"
    normalized = normalize_isbn(raw)
    assert normalized == "0306406152"
    assert is_valid_isbn10(normalized)
    assert is_valid_isbn(normalized)


def test_invalid_isbn():
    assert not is_valid_isbn("12345")
    assert is_valid_isbn13("9780306406157")
    assert is_valid_isbn("9780306406157")
