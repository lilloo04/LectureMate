"""PDF extraction tests using locally generated fixtures."""

import io

import pytest

fitz = pytest.importorskip("fitz")

from src.pdf_processor import extract_text


def make_pdf(pages=("Machine learning lecture",), encrypted=False):
    """Create a small PDF fixture."""
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
    """Preserve page order and file position."""
    data = make_pdf(("First lecture", "Second lecture"))
    assert "First lecture" in extract_text(data)
    assert extract_text(data).index("First lecture") < extract_text(data).index("Second lecture")
    stream = io.BytesIO(data)
    stream.seek(4)
    assert "First lecture" in extract_text(stream)
    assert stream.tell() == 4


def test_empty_and_invalid_pdf():
    """Reject empty and corrupt PDF inputs."""
    with pytest.raises(ValueError, match="비어"):
        extract_text(b"")
    with pytest.raises(ValueError, match="읽을 수"):
        extract_text(b"not a pdf")


def test_scanned_only_and_encrypted():
    """Reject scanned and encrypted PDF inputs."""
    with pytest.raises(ValueError, match="스캔 PDF"):
        extract_text(make_pdf(("",)))
    with pytest.raises(ValueError, match="암호화"):
        extract_text(make_pdf(encrypted=True))


def test_invalid_type_and_oversized():
    """Reject invalid argument types and oversized PDFs."""
    with pytest.raises(TypeError):
        extract_text("file.pdf")
    with pytest.raises(ValueError, match="25MB"):
        extract_text(b"x" * (25 * 1024 * 1024 + 1))

class ShortReadStream:
    """Stream that returns fewer bytes than requested, without getvalue."""

    def __init__(self, data):
        """Wrap a BytesIO stream."""
        self.stream = io.BytesIO(data)

    def seek(self, position):
        """Set the wrapped stream position."""
        return self.stream.seek(position)

    def tell(self):
        """Return the wrapped stream position."""
        return self.stream.tell()

    def read(self, size=-1):
        """Read no more than 97 bytes at once."""
        return self.stream.read(min(size, 97))


class GuardedStream:
    """Large stream that rejects unbounded reads."""

    def __init__(self):
        """Initialize synthetic stream state."""
        self.remaining = 25 * 1024 * 1024 + 100
        self.position = 0
        self.calls = 0

    def tell(self):
        """Return the stream position."""
        return self.position

    def seek(self, position):
        """Restore the stream position."""
        self.position = position

    def read(self, size=-1):
        """Return a bounded chunk."""
        assert 0 < size <= 64 * 1024
        self.calls += 1
        length = min(size, self.remaining)
        self.remaining -= length
        self.position += length
        return b"x" * length


def test_short_reads_and_position_restoration():
    """Consume short reads and restore the caller's position."""
    stream = ShortReadStream(make_pdf(("First", "Second")))
    stream.seek(2)
    assert "First" in extract_text(stream)
    assert "Second" in extract_text(stream)
    assert stream.tell() == 2


def test_oversized_stream_is_bounded():
    """Avoid unbounded reads and restore position on failure."""
    stream = GuardedStream()
    with pytest.raises(ValueError, match="25MB"):
        extract_text(stream)
    assert stream.calls > 1
    assert stream.tell() == 0
