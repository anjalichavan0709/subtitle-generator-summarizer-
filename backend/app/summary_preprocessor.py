import re
from collections import Counter
from typing import List


FILLER_PHRASES = [
    "we're going to",
    "we are going to",
    "i'm going to",
    "i am going to",
    "let's",
    "let us",
    "first of all",
    "welcome to",
    "today we're going to",
    "today we are going to",
    "the speaker says",
    "the lecturer says",
]


STOPWORDS = {
    "the", "and", "for", "that", "this", "with", "from", "have", "has",
    "are", "was", "were", "you", "your", "they", "their", "our", "will",
    "would", "could", "should", "there", "here", "what", "when", "where",
    "which", "about", "into", "than", "then", "just", "also", "because",
    "been", "being", "does", "done", "some", "very", "more", "most",
    "can", "may", "might", "must", "shall", "make", "made", "much",
    "thing", "things", "something", "anything", "everything", "actually",
    "basically", "probably", "maybe", "really", "right", "okay", "ok",
    "lecture", "today", "last", "time", "point", "points", "example",
    "examples", "question", "answer", "problem", "course", "class",
    "content", "provided", "license", "support", "materials", "donation",
    "video", "audio", "transcript", "speaker", "student", "students",
    "learn", "learning", "lesson", "topic", "topics",
}


ACADEMIC_CUES = {
    "concept", "definition", "method", "process", "model", "relationship",
    "application", "analysis", "result", "principle", "evidence", "reason",
    "compare", "explain", "describe", "important", "main", "key",
    "introduce", "develop", "show", "demonstrate", "connect", "interpret",
}


SOURCE_PATTERNS = [
    "creative commons",
    "copyright",
    "license",
    "all rights reserved",
    "make a donation",
    "view additional materials",
    "subscribe",
    "like and share",
    "visit our website",
]


CONCEPT_PATTERNS: list[str] = []


def clean_transcript_text(transcript_text: str) -> str:
    """
    Clean transcript text using only generic text normalization.

    The goal is to remove formatting noise without adding topic-specific fixes.
    """

    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty. Cannot summarize empty transcript.")

    text = transcript_text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def split_into_sentences(text: str) -> List[str]:
    raw_sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = []

    for sentence in raw_sentences:
        sentence = sentence.strip()
        word_count = len(sentence.split())

        if 6 <= word_count <= 55:
            sentences.append(sentence)

    return sentences


def remove_filler_language(sentence: str) -> str:
    cleaned = sentence.strip()

    for phrase in FILLER_PHRASES:
        cleaned = re.sub(re.escape(phrase), "", cleaned, flags=re.IGNORECASE)

    cleaned = re.sub(r"\b(I|i|we|We|our|Our|us|let's|Let's|you|You)\b", "", cleaned)
    cleaned = re.sub(r"\b(all right|okay|ok|so|now)\b[:,]?", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" ,.-")

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def is_useful_sentence(sentence: str) -> bool:
    lowered = sentence.lower()

    if any(pattern in lowered for pattern in SOURCE_PATTERNS):
        return False

    weak_patterns = [
        r"\bi\b",
        r"\bwe\b",
        r"\bour\b",
        r"\bus\b",
        r"\blet's\b",
        "going to",
        "get started",
        "welcome",
        "speaker says",
        "lecturer says",
    ]

    for pattern in weak_patterns:
        if re.search(pattern, lowered):
            return False

    return 6 <= len(sentence.split()) <= 60


def extract_keywords(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def score_sentence(sentence: str, keyword_counts: Counter) -> float:
    """
    Score a sentence using topic-neutral signals.

    Scoring uses repeated transcript keywords, general academic cues,
    and readable sentence length. It does not use any domain-specific list.
    """

    keywords = extract_keywords(sentence)

    if not keywords:
        return 0.0

    score = sum(min(keyword_counts.get(word, 0), 6) for word in keywords)

    lowered = sentence.lower()

    for cue in ACADEMIC_CUES:
        if re.search(rf"\b{re.escape(cue)}\b", lowered):
            score += 2.0

    word_count = len(sentence.split())

    if 12 <= word_count <= 30:
        score += 3.0
    elif 31 <= word_count <= 45:
        score += 1.0

    return score


def select_important_sentences(text: str, max_sentences: int = 10) -> List[str]:
    raw_sentences = split_into_sentences(text)
    cleaned_sentences = []

    for sentence in raw_sentences:
        cleaned = remove_filler_language(sentence)

        if cleaned and is_useful_sentence(cleaned):
            cleaned_sentences.append(cleaned)

    if not cleaned_sentences:
        return []

    all_keywords = []

    for sentence in cleaned_sentences:
        all_keywords.extend(extract_keywords(sentence))

    keyword_counts = Counter(all_keywords)

    scored_sentences = []

    for index, sentence in enumerate(cleaned_sentences):
        score = score_sentence(sentence, keyword_counts)

        # Earlier sentences often introduce the central topic of an educational video.
        score += max(0, 2.0 - index * 0.03)

        scored_sentences.append((score, index, sentence))

    scored_sentences.sort(reverse=True)

    selected = []
    used_keywords = set()

    for score, index, sentence in scored_sentences:
        sentence_keywords = set(extract_keywords(sentence))

        if not sentence_keywords:
            continue

        overlap = used_keywords.intersection(sentence_keywords)

        if selected and len(overlap) / len(sentence_keywords) > 0.65:
            continue

        selected.append((index, sentence))
        used_keywords.update(sentence_keywords)

        if len(selected) >= max_sentences:
            break

    selected.sort(key=lambda item: item[0])
    return [sentence for _, sentence in selected]


def build_model_input(important_sentences: List[str]) -> str:
    if not important_sentences:
        return ""

    concepts = extract_concept_terms(important_sentences, max_terms=8)
    concept_line = ", ".join(concepts)
    sentence_block = "\n".join(f"- {sentence}" for sentence in important_sentences[:8])

    if concept_line:
        return f"Key concepts: {concept_line}\nClean notes:\n{sentence_block}"

    return f"Clean notes:\n{sentence_block}"


def extract_concept_terms(important_sentences: List[str], max_terms: int = 8) -> List[str]:
    """
    Extract concept terms from the transcript itself.

    This avoids hardcoded subject keywords and keeps preprocessing generic.
    """

    text = " ".join(important_sentences)
    keyword_counts = Counter(extract_keywords(text))

    return [keyword for keyword, _ in keyword_counts.most_common(max_terms)]


def _join_concepts(concepts: List[str]) -> str:
    if not concepts:
        return "the main ideas"

    if len(concepts) == 1:
        return concepts[0]

    if len(concepts) == 2:
        return f"{concepts[0]} and {concepts[1]}"

    return f"{', '.join(concepts[:-1])}, and {concepts[-1]}"


def build_concept_fallback(important_sentences: List[str], max_words: int) -> str:
    """
    Build a generic extractive fallback from selected transcript sentences.

    The fallback does not invent a subject-specific summary. It uses the
    strongest selected transcript sentences when model output is weak.
    """

    if not important_sentences:
        return "The video explains the main ideas in a structured educational format."

    selected_sentences = important_sentences[:4]
    summary = " ".join(selected_sentences)
    words = summary.split()

    if len(words) > max_words:
        summary = " ".join(words[:max_words]).strip()
        if not summary.endswith((".", "!", "?")):
            summary += "."

    return summary


def build_extractive_fallback(important_sentences: List[str], max_words: int) -> str:
    return build_concept_fallback(important_sentences, max_words)
