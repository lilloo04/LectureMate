"""Keyword tests do not download model weights."""

from unittest.mock import Mock

import pytest

from src import keyword_extractor as keywords


def test_keywords_deduplicate_and_limit(monkeypatch):
    """Return no more than ten distinct phrases."""
    candidates = [("머신러닝", 0.9), ("머신러닝", 0.8), ("지도 학습", 0.7)]
    candidates += [(f"keyword{i}", 0.5) for i in range(15)]
    model = Mock()
    model.extract_keywords.return_value = candidates
    monkeypatch.setattr(keywords, "_get_model", lambda: model)
    result = keywords.extract_keywords("머신러닝과 지도 학습을 다룹니다")
    assert result[:2] == ["머신러닝", "지도 학습"]
    assert len(result) == 10
    model.extract_keywords.assert_called_once()


def test_empty_text():
    """Reject empty or tokenless input."""
    for text in ("", "   ", "!!!"):
        with pytest.raises(ValueError):
            keywords.extract_keywords(text)


def test_model_error(monkeypatch):
    """Surface model-loading errors."""
    def fail():
        """Simulate model-loading failure."""
        raise RuntimeError("no model")
    monkeypatch.setattr(keywords, "_get_model", fail)
    with pytest.raises(RuntimeError, match="키워드 추출"):
        keywords.extract_keywords("머신러닝 학습 데이터")


def test_model_extraction_error(monkeypatch):
    """Surface extraction errors."""
    model = Mock()
    model.extract_keywords.side_effect = OSError("model failed")
    monkeypatch.setattr(keywords, "_get_model", lambda: model)
    with pytest.raises(RuntimeError, match="키워드 추출"):
        keywords.extract_keywords("머신러닝 학습 데이터")

def test_keyword_filtering_casefold_and_empty_result(monkeypatch):
    """Filter stop words, invalid phrases, and case-insensitive duplicates."""
    model = Mock()
    model.extract_keywords.return_value = [
        ("Machine", 0.9), ("machine", 0.8), ("그리고", 0.7),
        ("!!!", 0.6), ("지도 학습", 0.5),
    ]
    monkeypatch.setattr(keywords, "_get_model", lambda: model)
    assert keywords.extract_keywords("Machine 지도 학습 그리고") == ["Machine", "지도 학습"]
    model.extract_keywords.return_value = [("그리고", 0.9), ("!!!", 0.7)]
    with pytest.raises(ValueError, match="유효한 키워드"):
        keywords.extract_keywords("Machine 지도 학습")


def test_long_input_keeps_head_and_tail(monkeypatch):
    """Bound long model inputs while retaining document ends."""
    model = Mock()
    model.extract_keywords.return_value = [("머신러닝", 0.9)]
    monkeypatch.setattr(keywords, "_get_model", lambda: model)
    text = "HEAD " + ("중간 " * 6000) + "TAIL"
    keywords.extract_keywords(text)
    actual = model.extract_keywords.call_args.args[0]
    assert len(actual) <= keywords._MAX_INPUT_CHARS + 1
    assert actual.startswith("HEAD")
    assert actual.endswith("TAIL")


def test_invalid_input_type():
    """Reject non-string input before model loading."""
    with pytest.raises(ValueError, match="텍스트"):
        keywords.extract_keywords(None)


def test_model_loading_error_is_wrapped(monkeypatch):
    """Preserve the original loader exception as the cause."""
    def broken():
        """Simulate a loader failure."""
        raise RuntimeError("download failed")

    monkeypatch.setattr(keywords, "_get_model", broken)
    with pytest.raises(RuntimeError, match="키워드 추출") as error:
        keywords.extract_keywords("머신러닝 지도학습")
    assert isinstance(error.value.__cause__, RuntimeError)
