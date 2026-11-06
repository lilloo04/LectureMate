# Public module contracts (v1)

The team must agree before changing these signatures or schemas.

```python
# A — PDF file-like object from Streamlit or binary PDF bytes; returns extracted text
extract_text(pdf_file) -> str

# A — returns up to 10 unique, meaningful Korean/English keywords
extract_keywords(text: str) -> list[str]

# B — returns a readable Korean summary string
summarize(text: str) -> str

# C — returns up to 5 validated quiz dictionaries
generate_quiz(text: str) -> list[dict]
```

Each quiz dictionary must have:

```python
{
    "question": "질문",
    "options": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
    "answer_index": 0,  # 0-based integer from 0 to 3
    "explanation": "정답 해설"
}
```

## Failure behavior
- Empty/unreadable/scanned PDF: raise `ValueError` with a useful message; do not pretend OCR was performed.
- Empty input text: raise `ValueError`.
- Model unavailable or generation invalid: raise a clear exception; caller displays an error. Do not return invented content.
- Quiz: every question has exactly 4 non-empty, distinct options and a valid answer index. Invalid questions must not be displayed as valid.
- Streamlit is responsible for showing errors and scoring answers; it must not depend on implementation internals.

## Input limits and performance
Start with short text PDFs; validate real Korean-language output and CPU runtime before promising long-document support. Model choices and truncation/chunking policy must be documented by B/C and approved before changing behavior.
