"""Extract Korean and English key phrases with a multilingual KeyBERT model."""

import re
from functools import lru_cache

_MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
_MAX_INPUT_CHARS = 20_000
_TOKEN_PATTERN = r"(?u)\b[가-힣A-Za-z][가-힣A-Za-z0-9]{1,}\b"
_STOP_WORDS = frozenset({
    "그리고", "그러나", "따라서", "또한", "대한", "통해", "위한", "있는", "있다", "한다",
    "하는", "된다", "것이다", "이러한", "이번", "강의", "내용", "설명", "예시", "경우",
    "the", "and", "for", "with", "from", "this", "that", "are", "was", "were",
})


@lru_cache(maxsize=1)
def _get_model():
    """Load once per process; model weights may download on first run."""
    try:
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer

        encoder = SentenceTransformer(_MODEL_NAME)
        return KeyBERT(model=encoder)
    except Exception as exc:
        raise RuntimeError("키워드 AI 모델을 불러오지 못했습니다. 설치와 네트워크를 확인해 주세요.") from exc


def extract_keywords(text: str) -> list[str]:
    """Return up to ten distinct, relevant Korean/English keywords or short phrases."""
    if not isinstance(text, str) or not text.strip():
        raise ValueError("키워드를 추출할 텍스트가 없습니다.")
    normalized = re.sub(r"\s+", " ", text).strip()
    if not re.search(_TOKEN_PATTERN, normalized):
        raise ValueError("키워드 후보가 될 단어가 없습니다.")
    # Keep model input bounded on CPU. Preserve both beginning and end of long documents.
    if len(normalized) > _MAX_INPUT_CHARS:
        half = _MAX_INPUT_CHARS // 2
        normalized = normalized[:half] + " " + normalized[-half:]
    try:
        from sklearn.feature_extraction.text import CountVectorizer

        vectorizer = CountVectorizer(
            token_pattern=_TOKEN_PATTERN,
            ngram_range=(1, 3),
            stop_words=list(_STOP_WORDS),
        )
        results = _get_model().extract_keywords(
            normalized,
            keyphrase_ngram_range=(1, 3),
            stop_words=list(_STOP_WORDS),
            top_n=30,
            use_mmr=True,
            diversity=0.4,
            vectorizer=vectorizer,
        )
    except Exception as exc:
        raise RuntimeError("키워드 추출에 실패했습니다. AI 모델 상태를 확인해 주세요.") from exc
    keywords = []
    seen = set()
    for phrase, _score in results:
        phrase = re.sub(r"\s+", " ", str(phrase)).strip()
        key = phrase.casefold()
        if not phrase or key in seen or key in _STOP_WORDS:
            continue
        if not re.search(_TOKEN_PATTERN, phrase):
            continue
        keywords.append(phrase)
        seen.add(key)
        if len(keywords) == 10:
            break
    if not keywords:
        raise ValueError("유효한 키워드를 찾지 못했습니다.")
    return keywords
