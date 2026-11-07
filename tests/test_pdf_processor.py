"""PDF extraction tests using locally generated fixtures."""

import io

import pytest

fitz = pytest.importorskip("fitz")

from src.pdf_processor import extract_text  # noqa: E402


def make_pdf(pages=("Machine learning lecture",), encrypted=False):
    doc = fitz.open()
    for content in pages:
        page = doc.new_page()
        if content:
            page.insert_text((50, 50), content)
    if encrypted:
        result = doc.tobytes(encryption=fitz.PDF_ENCRYPT_AES_256, owner_pw="owner", user_pw="secret")
    else:
        result = doc.tobytes()
    doc.close()
    return result


def test_extract_text_bytes_and_upload():
    data = make_pdf(("First lecture", "Second lecture"))
    assert "First lecture" in extract_text(data)
    assert extract_text(data).index("First lecture") < extract_text(data).index("Second lecture")
    stream = io.BytesIO(data)
    stream.seek(4)
    assert "First lecture" in extract_text(stream)
    assert stream.tell() == 4


def test_empty_and_invalid_pdf():
    with pytest.raises(ValueError, match="비어"):
        extract_text(b"")
    with pytest.raises(ValueError, match="읽을 수"):
        extract_text(b"not a pdf")


def test_scanned_only_and_encrypted():
    with pytest.raises(ValueError, match="스캔 PDF"):
        extract_text(make_pdf(("",)))
    with pytest.raises(ValueError, match="암호화"):
        extract_text(make_pdf(encrypted=True))


def test_invalid_type_and_oversized():
    with pytest.raises(ValueError):
        extract_text("file.pdf")
    with pytest.raises(ValueError, match="25MB"):
        extract_text(b"x" * (25 * 1024 * 1024 + 1))
