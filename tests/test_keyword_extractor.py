"""Keyword tests do not download model weights."""

from unittest.mock import Mock

import pytest

from src import keyword_extractor as keywords


def test_keywords_deduplicate_and_limit(monkeypatch):
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
    for text in ("", "   ", "!!!"):
        with pytest.raises(ValueError):
            keywords.extract_keywords(text)


def test_model_error(monkeypatch):
    def fail():
        raise RuntimeError("no model")
    monkeypatch.setattr(keywords, "_get_model", fail)
    with pytest.raises(RuntimeError, match="키워드 추출"):
        keywords.extract_keywords("머신러닝 학습 데이터")


def test_model_extraction_error(monkeypatch):
    model = Mock()
    model.extract_keywords.side_effect = OSError("model failed")
    monkeypatch.setattr(keywords, "_get_model", lambda: model)
    with pytest.raises(RuntimeError, match="키워드 추출"):
        keywords.extract_keywords("머신러닝 학습 데이터")
