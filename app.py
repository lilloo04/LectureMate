"""D: Streamlit interface and integration."""
import streamlit as st

st.set_page_config(page_title="LectureMate Lite", page_icon="📚")
st.title("📚 LectureMate Lite")
st.caption("PDF 요약 · 핵심 키워드 · 객관식 퀴즈")
uploaded_file = st.file_uploader("강의 PDF를 업로드하세요", type=["pdf"])
if uploaded_file is not None:
    st.info("PDF 분석 기능은 각 담당 모듈 구현 후 연결됩니다.")
