"""Generate validated multiple-choice quizzes from lecture text.

The public contract is ``generate_quiz(text) -> list[dict]``. No generative
model is selected here: choosing or downloading one needs approval. The model
boundary is ``_generate_quiz_candidates``. It must return model-produced items
or raise, and must not invent quizzes when generation is unavailable.
"""

import re

_MAX_QUIZZES = 5
_OPTION_COUNT = 4


def generate_quiz(text: str) -> list[dict]:
    """Return up to five validated quiz dictionaries.

    Each item has a question, four distinct options, a 0-based answer index,
    and an explanation. Invalid items are dropped. Empty input raises
    ValueError. A missing model or an entirely invalid generation raises
    RuntimeError instead of returning invented quizzes.
    """
    if not isinstance(text, str) or not text.strip():
        raise ValueError("퀴즈를 만들 텍스트가 없습니다.")
    normalized = re.sub(r"\s+", " ", text).strip()
    try:
        raw_items = _generate_quiz_candidates(normalized)
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError("퀴즈 생성에 실패했습니다. 모델 상태를 확인해 주세요.") from exc
    if not isinstance(raw_items, list):
        raise RuntimeError("퀴즈 생성 결과 형식이 올바르지 않습니다.")

    quizzes: list[dict] = []
    for item in raw_items:
        quiz = _normalize_quiz(item)
        if quiz is None:
            continue
        quizzes.append(quiz)
        if len(quizzes) == _MAX_QUIZZES:
            break
    if not quizzes:
        raise RuntimeError(
            "유효한 퀴즈를 만들지 못했습니다. 생성된 문항이 없거나 형식에 맞지 않습니다."
        )
    return quizzes


def _generate_quiz_candidates(text: str) -> list[dict]:
    """Return raw quiz dicts from the approved generator.

    No model is approved yet, so this does not download weights or invent items.
    """
    del text
    raise RuntimeError(
        "퀴즈 생성 모델이 아직 설정되지 않았습니다. "
        "모델을 승인하기 전에는 퀴즈를 만들지 않습니다."
    )


def _normalize_quiz(item: object) -> dict | None:
    """Return a contract-shaped quiz, or None when the item is not usable."""
    if not isinstance(item, dict):
        return None
    question = _clean_text(item.get("question"))
    explanation = _clean_text(item.get("explanation"))
    options = _clean_options(item.get("options"))
    answer_index = item.get("answer_index")
    if question is None or explanation is None or options is None:
        return None
    if isinstance(answer_index, bool) or not isinstance(answer_index, int):
        return None
    if not 0 <= answer_index < _OPTION_COUNT:
        return None
    return {
        "question": question,
        "options": options,
        "answer_index": answer_index,
        "explanation": explanation,
    }


def _clean_text(value: object) -> str | None:
    """Return stripped text, or None when the value is missing or blank."""
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned:
        return None
    return cleaned


def _clean_options(value: object) -> list[str] | None:
    """Return four distinct non-empty options, or None."""
    if not isinstance(value, list) or len(value) != _OPTION_COUNT:
        return None
    cleaned: list[str] = []
    for option in value:
        text = _clean_text(option)
        if text is None:
            return None
        cleaned.append(text)
    if len(set(cleaned)) != _OPTION_COUNT:
        return None
    return cleaned
