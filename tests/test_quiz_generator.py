"""Quiz tests mock the model boundary and do not download weights."""

import pytest

from src import quiz_generator as quiz


def _valid_item(index: int = 0) -> dict:
    """Build one contract-shaped quiz item."""
    return {
        "question": f"질문 {index}",
        "options": [f"보기{index}-1", f"보기{index}-2", f"보기{index}-3", f"보기{index}-4"],
        "answer_index": index % 4,
        "explanation": f"해설 {index}",
    }


def test_generate_quiz_returns_valid_items(monkeypatch):
    """Keep question, four distinct options, answer index, and explanation."""
    monkeypatch.setattr(
        quiz,
        "_generate_quiz_candidates",
        lambda text: [_valid_item(0), _valid_item(1)],
    )
    result = quiz.generate_quiz("파이썬은 인터프리터 언어입니다.")
    assert len(result) == 2
    assert set(result[0]) == {"question", "options", "answer_index", "explanation"}
    assert result[0]["options"] == ["보기0-1", "보기0-2", "보기0-3", "보기0-4"]
    assert result[0]["answer_index"] == 0
    assert len(set(result[0]["options"])) == 4


def test_generate_quiz_limits_to_five(monkeypatch):
    """Return at most five validated quizzes, in generation order."""
    monkeypatch.setattr(
        quiz,
        "_generate_quiz_candidates",
        lambda text: [_valid_item(i) for i in range(8)],
    )
    result = quiz.generate_quiz("강의 본문입니다.")
    assert [item["question"] for item in result] == [f"질문 {i}" for i in range(5)]


def test_empty_text_raises_value_error():
    """Reject empty or whitespace-only input."""
    for text in ("", "   ", "\n\t"):
        with pytest.raises(ValueError, match="텍스트가 없습니다"):
            quiz.generate_quiz(text)


def test_non_string_input_raises_value_error():
    """Reject input that is not text."""
    with pytest.raises(ValueError, match="텍스트가 없습니다"):
        quiz.generate_quiz(None)


def test_duplicate_options_are_dropped(monkeypatch):
    """Do not return a quiz whose options repeat."""
    duplicated = _valid_item(0)
    duplicated["options"] = ["같은 보기", "같은 보기", "다른 보기", "또다른 보기"]
    monkeypatch.setattr(
        quiz,
        "_generate_quiz_candidates",
        lambda text: [duplicated, _valid_item(1)],
    )
    result = quiz.generate_quiz("강의 본문입니다.")
    assert [item["question"] for item in result] == ["질문 1"]


def test_duplicate_options_after_strip_are_dropped(monkeypatch):
    """Treat options as duplicates after surrounding whitespace is removed."""
    duplicated = _valid_item(0)
    duplicated["options"] = [" 정답 ", "정답", "오답 1", "오답 2"]
    monkeypatch.setattr(quiz, "_generate_quiz_candidates", lambda text: [duplicated])
    with pytest.raises(RuntimeError, match="유효한 퀴즈"):
        quiz.generate_quiz("강의 본문입니다.")


def test_invalid_answer_index_is_dropped(monkeypatch):
    """Drop indexes outside 0..3 and non-integer indexes such as bool."""
    out_of_range = _valid_item(0)
    out_of_range["answer_index"] = 4
    boolean_index = _valid_item(1)
    boolean_index["answer_index"] = True
    monkeypatch.setattr(
        quiz,
        "_generate_quiz_candidates",
        lambda text: [out_of_range, boolean_index, _valid_item(2)],
    )
    result = quiz.generate_quiz("강의 본문입니다.")
    assert len(result) == 1
    assert result[0]["answer_index"] == 2


def test_blank_option_is_dropped(monkeypatch):
    """Drop a quiz that has an empty option."""
    blank = _valid_item(0)
    blank["options"] = ["보기1", "  ", "보기3", "보기4"]
    monkeypatch.setattr(
        quiz,
        "_generate_quiz_candidates",
        lambda text: [blank, _valid_item(1)],
    )
    result = quiz.generate_quiz("강의 본문입니다.")
    assert [item["question"] for item in result] == ["질문 1"]


def test_all_invalid_items_raise_without_inventing(monkeypatch):
    """Fail when every generated item is invalid instead of filling gaps."""
    bad = _valid_item(0)
    bad["answer_index"] = -1
    monkeypatch.setattr(quiz, "_generate_quiz_candidates", lambda text: [bad])
    with pytest.raises(RuntimeError, match="유효한 퀴즈"):
        quiz.generate_quiz("강의 본문입니다.")


def test_parse_generated_json():
    """Parse valid JSON returned by the model."""
    generated = """
    [
        {
            "question": "파이썬은 무엇인가요?",
            "options": ["언어", "운영체제", "하드웨어", "데이터베이스"],
            "answer_index": 0,
            "explanation": "파이썬은 프로그래밍 언어입니다."
        }
    ]
    """

    result = quiz._parse_generated_json(generated)

    assert len(result) == 1
    assert result[0]["answer_index"] == 0


def test_invalid_generated_json_raises_runtime_error():
    """Reject malformed JSON from the model."""
    with pytest.raises(RuntimeError):
        quiz._parse_generated_json("잘못된 JSON 출력")