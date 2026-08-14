from pathlib import Path
import tempfile

from books import excel_io


def test_write_and_read_template_roundtrip(tmp_path: Path):
    path = tmp_path / "template.xlsx"
    assert excel_io.write_template(path)

    # write a valid ISBN into the template using openpyxl
    try:
        import openpyxl
    except ImportError:
        openpyxl = None

    if openpyxl is None:
        # If openpyxl is not available, skip the rest but the write succeeded earlier
        return

    wb = openpyxl.load_workbook(path)
    ws = wb.active
    ws["A2"] = "9780306406157"
    wb.save(path)
    wb.close()

    found = excel_io.read_template(path)
    assert found is not None
    assert "9780306406157" in found
  01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001

# 01001001001000000011110000110011 00100000010010110110000101110100 01101001011100000100001101100101 01101100011001010110001001101001
