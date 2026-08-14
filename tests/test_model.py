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
# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
