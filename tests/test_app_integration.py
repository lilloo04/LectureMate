"""Integration tests for D (app.py pipeline, quiz validation, and grading)."""

from __future__ import annotations

import pytest

import app as app_module


def _sample_quizzes() -> list[dict]:
    return [
        {
            "question": "운영체제에서 프로세스와 스레드의 차이로 옳은 것은?",
            "options": [
                "스레드는 독립된 메모리 공간을 가진다",
                "같은 프로세스의 스레드는 코드·데이터·힙을 공유한다",
                "프로세스 전환은 스레드 전환보다 항상 빠르다",
                "스레드는 CPU를 사용할 수 없다",
            ],
            "answer_index": 1,
            "explanation": "동일 프로세스 내 스레드는 자원 일부를 공유합니다.",
        },
        {
            "question": "교착상태(Deadlock) 발생 조건이 아닌 것은?",
            "options": [
                "상호 배제",
                "점유와 대기",
                "비선점",
                "가상 메모리 페이징",
            ],
            "answer_index": 3,
            "explanation": "가상 메모리 페이징은 교착상태 필요조건이 아닙니다.",
        },
    ]


def test_run_lecture_pipeline_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module, "extract_text", lambda _: "강의 본문 텍스트입니다.")
    monkeypatch.setattr(app_module, "summarize", lambda _: "핵심 요약입니다.")
    monkeypatch.setattr(
        app_module,
        "extract_keywords",
        lambda _: ["운영체제", "스레드", "운영체제", "교착상태"],
    )
    monkeypatch.setattr(app_module, "generate_quiz", lambda _: _sample_quizzes())

    result = app_module.run_lecture_pipeline(object())

    assert result["text"] == "강의 본문 텍스트입니다."
    assert result["summary"] == "핵심 요약입니다."
    assert result["keywords"] == ["운영체제", "스레드", "교착상태"]
    assert len(result["quizzes"]) == 2
    assert result["summary_error"] is None
    assert result["keywords_error"] is None
    assert result["quiz_error"] is None


def test_run_lecture_pipeline_raises_on_empty_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app_module, "extract_text", lambda _: "   \n  ")

    with pytest.raises(ValueError):
        app_module.run_lecture_pipeline(object())


def test_validate_quiz_items_filters_malformed_entries() -> None:
    malformed_and_valid = [
        {
            "question": "유효한 문제",
            "options": ["A", "B", "C", "D"],
            "answer_index": 2,
            "explanation": "정답은 C입니다.",
        },
        {
            "question": "중복 선택지 문제",
            "options": ["동일", "동일", "C", "D"],
            "answer_index": 0,
            "explanation": "중복 선택지는 무효입니다.",
        },
        {
            "question": "범위 밖 인덱스 문제",
            "options": ["A", "B", "C", "D"],
            "answer_index": 4,
            "explanation": "인덱스 오류",
        },
        {
            "question": "불리언 인덱스 문제",
            "options": ["A", "B", "C", "D"],
            "answer_index": True,
            "explanation": "bool은 int로 취급하지 않습니다.",
        },
    ]

    valid = app_module.validate_quiz_items(malformed_and_valid)
    assert len(valid) == 1
    assert valid[0]["question"] == "유효한 문제"
    assert valid[0]["answer_index"] == 2


def test_score_quiz_calculates_score_and_details() -> None:
    quizzes = _sample_quizzes()
    selected = {0: 1, 1: 0}

    correct, total, details = app_module.score_quiz(quizzes, selected)

    assert correct == 1
    assert total == 2
    assert details[0]["is_correct"] is True
    assert details[1]["is_correct"] is False
    assert details[1]["selected_option"] == "상호 배제"
    assert details[1]["answer_option"] == "가상 메모리 페이징"