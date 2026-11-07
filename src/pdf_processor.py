"""Extract text from lecture PDFs without OCR."""

import re
from typing import BinaryIO

import fitz

_MAX_PDF_BYTES = 25 * 1024 * 1024
_MAX_PAGES = 200


def _read_pdf_bytes(pdf_file: BinaryIO | bytes) -> bytes:
    """Read bytes without changing the caller's file position when possible."""
    if isinstance(pdf_file, bytes):
        return pdf_file
    if hasattr(pdf_file, "getvalue"):
        data = pdf_file.getvalue()
    elif hasattr(pdf_file, "read"):
        position = pdf_file.tell() if hasattr(pdf_file, "tell") else None
        try:
            data = pdf_file.read()
        finally:
            if position is not None and hasattr(pdf_file, "seek"):
                pdf_file.seek(position)
    else:
        raise ValueError("PDF 파일 또는 PDF 바이트를 전달해 주세요.")
    if not isinstance(data, bytes):
        raise ValueError("PDF 파일을 바이너리 모드로 읽어 주세요.")
    return data


def _clean_text(text: str) -> str:
    """Normalize spacing while retaining paragraph and page boundaries."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [re.sub(r"[\t \u00a0]+", " ", line).strip() for line in text.split("\n")]
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def extract_text(pdf_file) -> str:
    """Return readable text from a PDF upload or bytes; reject scanned-only PDFs."""
    data = _read_pdf_bytes(pdf_file)
    if not data:
        raise ValueError("PDF 파일이 비어 있습니다.")
    if len(data) > _MAX_PDF_BYTES:
        raise ValueError("PDF 크기는 25MB 이하여야 합니다.")
    try:
        with fitz.open(stream=data, filetype="pdf") as document:
            if document.needs_pass:
                raise ValueError("암호화된 PDF는 지원하지 않습니다. 암호를 해제해 주세요.")
            if document.page_count > _MAX_PAGES:
                raise ValueError("PDF는 최대 200페이지까지 지원합니다.")
            pages = [_clean_text(page.get_text(sort=True)) for page in document]
    except ValueError:
        raise
    except (fitz.FileDataError, fitz.EmptyFileError, RuntimeError) as exc:
        raise ValueError("PDF를 읽을 수 없습니다. 손상되지 않은 PDF인지 확인해 주세요.") from exc
    text = "\n\n".join(page for page in pages if page).strip()
    if not text:
        raise ValueError("추출 가능한 텍스트가 없습니다. 스캔 PDF는 OCR 없이 지원하지 않습니다.")
    return text
