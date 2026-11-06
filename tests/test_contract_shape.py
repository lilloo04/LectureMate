"""Lightweight schema example; AI model tests should mock model calls."""


def test_quiz_schema_example():
    quiz = {
        "question": "Python의 특징은?",
        "options": ["인터프리터 언어", "하드웨어", "운영체제", "데이터베이스"],
        "answer_index": 0,
        "explanation": "Python은 인터프리터 언어입니다.",
    }
    assert len(quiz["options"]) == 4
    assert 0 <= quiz["answer_index"] < len(quiz["options"])
    assert len(set(quiz["options"])) == 4
