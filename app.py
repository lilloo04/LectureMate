"""D: Streamlit interface and integration for LectureMate Lite."""

from __future__ import annotations

from typing import Any

import streamlit as st

from src.keyword_extractor import extract_keywords
from src.pdf_processor import extract_text
from src.quiz_generator import generate_quiz
from src.summarizer import summarize


def validate_quiz_items(raw_quizzes: Any) -> list[dict[str, Any]]:
    """Return only quiz items that match CONTRACTS.md schema."""
    if not isinstance(raw_quizzes, list):
        return []

    valid_quizzes: list[dict[str, Any]] = []
    for item in raw_quizzes[:5]:
        if not isinstance(item, dict):
            continue

        question = item.get("question")
        options = item.get("options")
        answer_index = item.get("answer_index")
        explanation = item.get("explanation")

        if not isinstance(question, str) or not question.strip():
            continue
        if not isinstance(options, list) or len(options) != 4:
            continue
        if not all(isinstance(opt, str) and opt.strip() for opt in options):
            continue
        if len({opt.strip() for opt in options}) != 4:
            continue
        if isinstance(answer_index, bool) or not isinstance(answer_index, int):
            continue
        if not (0 <= answer_index <= 3):
            continue
        if not isinstance(explanation, str) or not explanation.strip():
            continue

        valid_quizzes.append(
            {
                "question": question.strip(),
                "options": [opt.strip() for opt in options],
                "answer_index": answer_index,
                "explanation": explanation.strip(),
            }
        )

    return valid_quizzes


def score_quiz(
    quizzes: list[dict[str, Any]],
    selected_answers: dict[int, int],
) -> tuple[int, int, list[dict[str, Any]]]:
    """Grade selected answers against validated quiz items."""
    total = len(quizzes)
    correct_count = 0
    details: list[dict[str, Any]] = []

    for idx, quiz in enumerate(quizzes):
        selected_idx = selected_answers.get(idx)
        answer_idx = quiz["answer_index"]
        is_correct = selected_idx == answer_idx
        if is_correct:
            correct_count += 1

        options = quiz["options"]
        details.append(
            {
                "index": idx,
                "question": quiz["question"],
                "selected_index": selected_idx,
                "selected_option": (
                    options[selected_idx]
                    if isinstance(selected_idx, int) and 0 <= selected_idx < len(options)
                    else "미선택"
                ),
                "answer_index": answer_idx,
                "answer_option": options[answer_idx],
                "is_correct": is_correct,
                "explanation": quiz["explanation"],
            }
        )

    return correct_count, total, details


def run_lecture_pipeline(pdf_file: Any) -> dict[str, Any]:
    """Execute PDF extraction, summarization, keyword extraction, and quiz generation."""
    text = extract_text(pdf_file)
    if not isinstance(text, str) or not text.strip():
        raise ValueError("PDF에서 추출된 텍스트가 비어 있습니다. 텍스트 기반 PDF인지 확인해 주세요.")

    result: dict[str, Any] = {
        "text": text,
        "summary": None,
        "summary_error": None,
        "keywords": [],
        "keywords_error": None,
        "quizzes": [],
        "quiz_error": None,
    }

    try:
        summary = summarize(text)
        if not isinstance(summary, str) or not summary.strip():
            raise ValueError("요약 결과가 비어 있습니다.")
        result["summary"] = summary.strip()
    except Exception as exc:
        result["summary_error"] = f"AI 요약 중 오류가 발생했습니다: {exc}"

    try:
        raw_keywords = extract_keywords(text)
        if not isinstance(raw_keywords, list):
            raise ValueError("키워드 출력 형식이 올바르지 않습니다.")
        cleaned_keywords: list[str] = []
        seen: set[str] = set()
        for kw in raw_keywords:
            if isinstance(kw, str) and kw.strip():
                token = kw.strip()
                key = token.lower()
                if key not in seen:
                    seen.add(key)
                    cleaned_keywords.append(token)
            if len(cleaned_keywords) >= 10:
                break
        result["keywords"] = cleaned_keywords
    except Exception as exc:
        result["keywords_error"] = f"키워드 추출 중 오류가 발생했습니다: {exc}"

    try:
        raw_quizzes = generate_quiz(text)
        validated = validate_quiz_items(raw_quizzes)
        if raw_quizzes and not validated:
            raise ValueError("생성된 퀴즈 형식이 유효하지 않아 표시할 수 없습니다.")
        result["quizzes"] = validated
    except Exception as exc:
        result["quiz_error"] = f"퀴즈 생성 중 오류가 발생했습니다: {exc}"

    return result


def _init_session_state() -> None:
    defaults: dict[str, Any] = {
        "file_signature": None,
        "analysis_result": None,
        "fatal_error": None,
        "selected_answers": {},
        "quiz_submitted": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def _render_summary_and_keywords(result: dict[str, Any]) -> None:
    col_summary, col_keywords = st.columns([2, 1])

    with col_summary:
        st.subheader("📝 AI 요약")
        if result.get("summary_error"):
            st.error(result["summary_error"])
        elif result.get("summary"):
            st.write(result["summary"])
        else:
            st.info("표시할 요약 결과가 없습니다.")

    with col_keywords:
        st.subheader("🔑 핵심 키워드")
        if result.get("keywords_error"):
            st.error(result["keywords_error"])
        elif result.get("keywords"):
            st.markdown(", ".join(f"`{kw}`" for kw in result["keywords"]))
        else:
            st.info("추출된 키워드가 없습니다.")


def _render_quiz_section(quizzes: list[dict[str, Any]], quiz_error: str | None) -> None:
    st.subheader("❓ 객관식 퀴즈")

    if quiz_error:
        st.error(quiz_error)

    if not quizzes:
        if not quiz_error:
            st.info("표시할 유효한 퀴즈 문항이 없습니다.")
        return

    selected_answers: dict[int, int] = st.session_state.selected_answers

    with st.form(key="quiz_form"):
        for idx, quiz in enumerate(quizzes):
            st.markdown(f"**Q{idx + 1}. {quiz['question']}**")
            default_idx = selected_answers.get(idx, 0)
            if not isinstance(default_idx, int) or not (0 <= default_idx < len(quiz["options"])):
                default_idx = 0

            chosen = st.radio(
                label=f"Q{idx + 1} 선택지",
                options=quiz["options"],
                index=default_idx,
                key=f"quiz_q_{idx}",
                label_visibility="collapsed",
            )
            selected_answers[idx] = quiz["options"].index(chosen)
            st.divider()

        submitted = st.form_submit_button("답안 제출 및 채점")

    if submitted:
        st.session_state.selected_answers = selected_answers
        st.session_state.quiz_submitted = True

    if st.session_state.quiz_submitted:
        correct_count, total, details = score_quiz(quizzes, st.session_state.selected_answers)
        st.success(f"채점 결과: {total}문항 중 {correct_count}문항 정답")

        for item in details:
            q_num = item["index"] + 1
            if item["is_correct"]:
                st.markdown(f"✅ **Q{q_num}. 정답** — {item['answer_option']}")
            else:
                st.markdown(
                    f"❌ **Q{q_num}. 오답** — 선택: {item['selected_option']} / "
                    f"정답: {item['answer_option']}"
                )
            st.caption(f"해설: {item['explanation']}")


def main() -> None:
    """Render the Streamlit application."""
    st.set_page_config(page_title="LectureMate Lite", page_icon="📚")
    st.title("📚 LectureMate Lite")
    st.caption("PDF 요약 · 핵심 키워드 · 객관식 퀴즈")

    _init_session_state()

    uploaded_file = st.file_uploader("강의 PDF를 업로드하세요", type=["pdf"])
    if uploaded_file is None:
        st.session_state.file_signature = None
        st.session_state.analysis_result = None
        st.session_state.fatal_error = None
        st.session_state.selected_answers = {}
        st.session_state.quiz_submitted = False
        return

    file_size = getattr(uploaded_file, "size", None)
    signature = (uploaded_file.name, file_size)

    if st.session_state.file_signature != signature:
        st.session_state.file_signature = signature
        st.session_state.analysis_result = None
        st.session_state.fatal_error = None
        st.session_state.selected_answers = {}
        st.session_state.quiz_submitted = False

        with st.spinner("PDF를 분석하고 요약·키워드·퀴즈를 생성하는 중입니다..."):
            try:
                st.session_state.analysis_result = run_lecture_pipeline(uploaded_file)
            except ValueError as exc:
                st.session_state.fatal_error = str(exc)
            except Exception as exc:
                st.session_state.fatal_error = f"PDF 처리 중 예기치 못한 오류가 발생했습니다: {exc}"

    if st.session_state.fatal_error:
        st.error(st.session_state.fatal_error)
        return

    result = st.session_state.analysis_result
    if not result:
        return

    with st.expander("추출된 강의 텍스트 보기", expanded=False):
        st.text_area(
            label="추출 텍스트",
            value=result["text"],
            height=200,
            disabled=True,
            label_visibility="collapsed",
        )

    _render_summary_and_keywords(result)
    st.divider()
    _render_quiz_section(result.get("quizzes", []), result.get("quiz_error"))


if __name__ == "__main__":
    main()