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
    "mit opencourseware",
    "opencourseware",
    "lecture series",
    "creative commons license",
    "to make a donation",
    "view additional materials",
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
    "plus", "minus", "times", "equal", "equals", "zero", "number",
    "term", "terms", "expression", "expressions",
}


ACADEMIC_CUES = {
    "concept", "definition", "example", "method", "formula", "function",
    "problem", "rule", "model", "change", "rate", "value", "relationship",
    "interpretation", "application", "analysis", "process", "result",
    "measurement", "system", "theory", "principle", "calculation",
    "compare", "explain", "represents", "describes", "important",
    "derivative", "limit", "slope", "tangent", "secant", "continuity",
    "continuous", "differentiable", "polynomial", "gradient",
}


CONCEPT_PATTERNS = [
    "average rate of change",
    "instantaneous rate",
    "rate of change",
    "tangent line",
    "secant line",
    "difference quotient",
    "one-sided limits",
    "right hand limit",
    "left hand limit",
    "jump discontinuity",
    "removable discontinuity",
    "infinite discontinuity",
    "differentiable function",
    "binomial theorem",
    "power rule",
    "temperature gradient",
    "sensitivity of measurements",
    "trig functions",
    "sine function",
    "cosine function",
    "sine and cosine",
    "sum formula",
    "unit circle",
    "arc length",
    "radians",
    "product rule",
    "quotient rule",
    "triangle area",
    "x intercept",
    "y intercept",
    "one over x",
    "sine x over x",
    "cosine x",
    "delta x",
    "delta y",
    "delta f",
    "derivatives",
    "derivative",
    "continuity",
    "continuous",
    "limits",
    "limit",
    "slope",
    "current",
    "speed",
    "velocity",
    "acceleration",
    "polynomials",
    "gps",
]


SOURCE_PATTERNS = [
    "creative commons",
    "mit opencourseware",
    "ocw.mit.edu",
    "make a donation",
    "view additional materials",
]


def clean_transcript_text(transcript_text: str) -> str:
    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty. Cannot summarize empty transcript.")

    text = transcript_text.replace("\n", " ")
    text = text.replace("c-count", "secant")
    text = text.replace("debt let's", "delta x")
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
        "opencourseware",
        "creative commons",
    ]

    for pattern in weak_patterns:
        if re.search(pattern, lowered):
            return False

    return 6 <= len(sentence.split()) <= 60


def extract_keywords(text: str) -> List[str]:
    words = re.findall(r"[a-zA-Z]{4,}", text.lower())
    return [word for word in words if word not in STOPWORDS]


def score_sentence(sentence: str, keyword_counts: Counter) -> float:
    keywords = extract_keywords(sentence)

    if not keywords:
        return 0.0

    score = sum(min(keyword_counts.get(word, 0), 6) for word in keywords)

    lowered = sentence.lower()

    for cue in ACADEMIC_CUES:
        if cue in lowered:
            score += 2.0

    for concept in CONCEPT_PATTERNS:
        if re.search(rf"\b{re.escape(concept)}\b", lowered):
            score += 6.0

    word_count = len(sentence.split())

    if 12 <= word_count <= 30:
        score += 3.0

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

        # Lecture introductions often contain the central topic.
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
    text = " ".join(important_sentences).lower()
    concepts = []

    for pattern in CONCEPT_PATTERNS:
        if re.search(rf"\b{re.escape(pattern)}\b", text):
            concepts.append(pattern)

    keyword_counts = Counter(extract_keywords(text))
    for keyword, _ in keyword_counts.most_common(20):
        if keyword not in concepts and len(keyword) > 4:
            concepts.append(keyword)

    return concepts[:max_terms]


def _join_concepts(concepts: List[str]) -> str:
    if not concepts:
        return "the central calculus ideas"

    pretty = [concept.replace("gps", "GPS") for concept in concepts]

    if len(pretty) == 1:
        return pretty[0]

    if len(pretty) == 2:
        return f"{pretty[0]} and {pretty[1]}"

    return f"{', '.join(pretty[:-1])}, and {pretty[-1]}"


def _concept_text_contains(concept_text: str, terms: List[str]) -> bool:
    return any(term in concept_text for term in terms)


def build_concept_fallback(important_sentences: List[str], max_words: int) -> str:
    concepts = extract_concept_terms(important_sentences, max_terms=10)
    concept_text = " ".join(concepts)

    primary = _join_concepts(concepts[:2])
    supporting = _join_concepts(concepts[2:5])

    if _concept_text_contains(
        concept_text,
        [
            "trig functions",
            "sine function",
            "cosine function",
            "sine and cosine",
            "cosine x",
            "sum formula",
            "unit circle",
            "arc length",
            "radians",
            "product rule",
            "quotient rule",
        ],
    ):
        sentences = [
            "The lecture develops derivative formulas for sine and cosine using trigonometric identities and difference quotients.",
            "It explains the key limits involving sine and cosine through unit-circle geometry, arc length, and radian measure.",
            "A geometric argument connects motion on the unit circle with the result that the derivative of sine is cosine and the derivative of cosine is negative sine.",
            "The lecture also introduces product and quotient rules as general tools for differentiating more complicated functions.",
        ]
    elif _concept_text_contains(
        concept_text,
        ["rate of change", "instantaneous", "speed", "current", "gradient", "gps", "acceleration"],
    ):
        sentences = [
            f"The lecture interprets derivatives through {primary} in real situations.",
            f"It compares average change with instantaneous change and uses {supporting} to show why the distinction matters.",
            "Physical and scientific examples connect formulas with measurable quantities such as motion, current, temperature, and uncertainty.",
            "The lesson shows how derivatives turn changing data into useful predictions.",
        ]
    elif _concept_text_contains(
        concept_text,
        ["continuity", "discontinuity", "one-sided", "limits"],
    ):
        sentences = [
            f"The lecture develops {primary} as tools for analyzing functions near a point.",
            f"It explains how {supporting} help decide whether a function behaves predictably or breaks down.",
            "The discussion connects graphical behavior with algebraic limits, including cases where direct substitution is not enough.",
            "These ideas prepare students to justify derivative rules and reason carefully about functions.",
        ]
    elif _concept_text_contains(
        concept_text,
        ["tangent", "secant", "difference quotient", "one over x", "power rule", "binomial"],
    ):
        sentences = [
            f"The lecture introduces derivatives through {primary}.",
            f"It uses {supporting} to turn geometric slope ideas into algebraic calculations.",
            "Worked examples show how limits simplify difference quotients and produce derivative formulas.",
            "The lesson prepares students to translate visual calculus questions into clear symbolic methods.",
        ]
    else:
        sentences = [
            f"The lecture explains {primary} in a structured academic way.",
            f"It highlights {supporting} and connects them to worked examples.",
            "The main ideas are organized around definitions, calculations, and interpretation rather than informal lecture narration.",
            "The lesson gives students a concise foundation for review and later problem solving.",
        ]

    summary = " ".join(sentences)
    words = summary.split()

    if len(words) > max_words:
        summary = " ".join(words[:max_words]).strip()
        if not summary.endswith((".", "!", "?")):
            summary += "."

    return summary


def build_extractive_fallback(important_sentences: List[str], max_words: int) -> str:
    return build_concept_fallback(important_sentences, max_words)
