
"""Generate validated multiple-choice quizzes from lecture text."""

import json
import re
from itertools import combinations

_MAX_QUIZZES = 5
_OPTION_COUNT = 4


def generate_quiz(text: str) -> list[dict]:
    """Return up to five validated rule-based quiz dictionaries."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("퀴즈를 만들 텍스트가 없습니다.")

    normalized = re.sub(r"\s+", " ", text).strip()

    try:
        raw_items = _generate_quiz_candidates(normalized)
    except Exception as exc:
        raise RuntimeError("퀴즈 생성에 실패했습니다.") from exc

    if not isinstance(raw_items, list):
        raise RuntimeError("퀴즈 생성 결과 형식이 올바르지 않습니다.")

    quizzes = []

    for item in raw_items:
        quiz = _normalize_quiz(item)

        if quiz is not None:
            quizzes.append(quiz)

        if len(quizzes) == _MAX_QUIZZES:
            break

    if not quizzes:
        raise RuntimeError(
            "유효한 퀴즈를 만들지 못했습니다. "
            "강의 내용에서 출제 가능한 정보를 찾지 못했습니다."
        )

    return quizzes


def _generate_quiz_candidates(text: str) -> list[dict]:
    """
    Generate quizzes from explicitly stated internal/external
    environment classifications in lecture text.
    """

    facts = _extract_category_facts(text)

    if not facts:
        return []

    terms = []
    seen_terms = set()

    for fact in facts:
        for term in (fact["left"], fact["right"]):
            key = term.casefold()

            if key not in seen_terms:
                terms.append(term)
                seen_terms.add(key)

    quizzes = []

    for fact in facts:
        category = fact["category"]
        left = fact["left"]
        right = fact["right"]

        correct_option = fact["items"]
        correct_key = frozenset((left.casefold(), right.casefold()))

        wrong_options = []

        for first, second in combinations(terms, 2):
            pair_key = frozenset(
                (first.casefold(), second.casefold())
            )

            if pair_key == correct_key:
                continue

            option = _format_pair(first, second)

            if option != correct_option and option not in wrong_options:
                wrong_options.append(option)

        if len(wrong_options) < 3:
            continue

        answer_index = len(quizzes) % _OPTION_COUNT

        options = wrong_options[:3]
        options.insert(answer_index, correct_option)

        question = (
            f"강의 내용에 따르면 기업의 {category} 환경에 "
            "포함되는 요소는 무엇인가요?"
        )

        explanation = (
            f"강의 내용에서는 기업의 {category} 환경에 해당하는 "
            f"요소로 '{correct_option}'를 제시합니다."
        )

        quizzes.append({
            "question": question,
            "options": options,
            "answer_index": answer_index,
            "explanation": explanation,
        })

        if len(quizzes) == _MAX_QUIZZES:
            break

    return quizzes


def _extract_category_facts(text: str) -> list[dict]:
    """Extract explicitly stated internal/external environment pairs."""

    patterns = [
        re.compile(
            r"(?P<category>내부|외부)\s*환경(?:에는|은|는)\s*"
            r"(?P<items>[^.!?。;\n]+?)\s*(?:이|가)\s*포함"
        ),
        re.compile(
            r"(?P<category>내부|외부)\s*환경을\s*구성하는\s*요소는\s*"
            r"(?P<items>[^.!?。;\n]+?)\s*(?:이다|입니다)"
        ),
    ]

    facts = []

    for pattern in patterns:
        for match in pattern.finditer(text):
            items = match.group("items").strip()

            parts = re.split(
                r"\s*(?:와|과|및)\s*",
                items,
                maxsplit=1,
            )

            if len(parts) != 2:
                continue

            left = parts[0].strip()
            right = parts[1].strip()

            if not left or not right:
                continue

            facts.append({
                "category": match.group("category"),
                "left": left,
                "right": right,
                "items": items,
            })

    return facts


def _has_final_consonant(word: str) -> bool:
    """Check whether the last Korean syllable has a final consonant."""

    for char in reversed(word):
        if "가" <= char <= "힣":
            return (ord(char) - ord("가")) % 28 != 0

    return False


def _format_pair(first: str, second: str) -> str:
    """Join two Korean terms using the appropriate conjunction."""

    conjunction = "과" if _has_final_consonant(first) else "와"

    return f"{first}{conjunction} {second}"


def _parse_generated_json(generated_text: str) -> list[dict]:
    """Keep JSON parsing compatibility with existing tests."""

    cleaned = generated_text.strip()

    cleaned = re.sub(
        r"^\s*```(?:json)?\s*|\s*```\s*$",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    match = re.search(r"\[[\s\S]*\]", cleaned)

    if match is None:
        raise RuntimeError("모델이 JSON 배열을 생성하지 않았습니다.")

    try:
        result = json.loads(match.group(0))
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "JSON 출력 형식이 잘못되었습니다."
        ) from exc

    if not isinstance(result, list):
        raise RuntimeError("JSON 배열이 아닙니다.")

    return result


def _normalize_quiz(item: object) -> dict | None:
    """Return a contract-shaped quiz, or None when invalid."""

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
    """Return stripped text, or None when missing or blank."""

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

    cleaned = []

    for option in value:
        text = _clean_text(option)

        if text is None:
            return None

        cleaned.append(text)

    if len(set(cleaned)) != _OPTION_COUNT:
        return None

    return cleaned
