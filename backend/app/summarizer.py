from pathlib import Path
import re

from app.config import (
    SUMMARIZATION_MODEL_NAME,
    MAX_SUMMARY_WORDS,
    SUMMARY_OUTPUT_DIR,
)
from app.logger import get_logger
from app.summary_preprocessor import (
    build_extractive_fallback,
    build_model_input,
    clean_transcript_text,
    select_important_sentences,
)

logger = get_logger(__name__)


FORBIDDEN_OUTPUT_TERMS = [
    "requirements",
    "lecture points",
    "clean notes",
    "key concepts",
    "academic summary",
    "summary:",
    "student summary",
    "under 100 words",
    "first-person",
    "speaker",
    "source",
    "channel",
    "do not copy",
    "going to",
    "get started",
    "mit opencourseware",
    "opencourseware",
    "lecture series",
]


def load_summarization_model():
    logger.info("Loading summarization model: %s", SUMMARIZATION_MODEL_NAME)

    try:
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError as error:
        raise RuntimeError(
            "Summarization dependencies are not installed. "
            "Install backend requirements to enable FLAN-T5 generation."
        ) from error

    tokenizer = AutoTokenizer.from_pretrained(SUMMARIZATION_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZATION_MODEL_NAME)

    return tokenizer, model


def generate_summary_with_model(clean_points: str, tokenizer, model) -> str:
    try:
        import torch
    except ImportError as error:
        raise RuntimeError(
            "PyTorch is not installed. Install backend requirements to enable FLAN-T5 generation."
        ) from error

    prompt = (
        "Create a concise student study summary from the notes below.\n"
        "Use 3 to 5 complete sentences in one paragraph.\n"
        "Use polished academic language and avoid copying note wording.\n\n"
        f"{clean_points}\n\n"
        "Summary:"
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=1024,
    )

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=120,
            min_new_tokens=30,
            num_beams=4,
            repetition_penalty=1.5,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True).strip()


def clean_summary(summary: str) -> str:
    cleaned = summary.strip()

    cleaned = re.sub(r"^(summary|student summary)\s*:\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\b(I|i|we|We|our|Our|us|let's|Let's)\b", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = cleaned.strip(" ,.-")

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def limit_summary_words(summary: str, max_words: int = MAX_SUMMARY_WORDS) -> str:
    words = summary.split()

    if len(words) <= max_words:
        return summary.strip()

    limited_summary = " ".join(words[:max_words]).strip()

    if not limited_summary.endswith((".", "!", "?")):
        limited_summary += "."

    return limited_summary


def count_summary_sentences(summary: str) -> int:
    sentences = re.split(r"(?<=[.!?])\s+", summary.strip())
    return len([sentence for sentence in sentences if sentence.strip()])


def has_prompt_leakage(summary: str) -> bool:
    lowered = summary.lower()

    for term in FORBIDDEN_OUTPUT_TERMS:
        if term in lowered:
            return True

    bullet_like_patterns = [
        r"-\s*3 to 5",
        r"-\s*no ",
        r"-\s*do not",
        r"requirements\s*:",
    ]

    for pattern in bullet_like_patterns:
        if re.search(pattern, lowered):
            return True

    return False


def has_first_person_language(summary: str) -> bool:
    lowered = summary.lower()

    first_person_patterns = [
        r"\bi\b",
        r"\bwe\b",
        r"\bour\b",
        r"\bus\b",
        r"\blet's\b",
    ]

    for pattern in first_person_patterns:
        if re.search(pattern, lowered):
            return True

    return False


def has_raw_transcript_copy(summary: str, important_sentences: list[str]) -> bool:
    lowered_summary = summary.lower()

    for sentence in important_sentences:
        lowered_sentence = sentence.lower().strip(" .!?")
        sentence_words = lowered_sentence.split()

        if len(sentence_words) < 12:
            continue

        if lowered_sentence in lowered_summary:
            return True

        for index in range(0, max(0, len(sentence_words) - 11)):
            phrase = " ".join(sentence_words[index:index + 12])
            if phrase in lowered_summary:
                return True

    return False


def is_summary_usable(summary: str, important_sentences: list[str] | None = None) -> bool:
    if not summary:
        return False

    if has_prompt_leakage(summary):
        return False

    if has_first_person_language(summary):
        return False

    word_count = len(summary.split())

    if word_count < 25:
        return False

    if word_count > MAX_SUMMARY_WORDS + 10:
        return False

    sentence_count = count_summary_sentences(summary)

    if sentence_count < 3 or sentence_count > 5:
        return False

    if important_sentences and has_raw_transcript_copy(summary, important_sentences):
        return False

    return True


def summarize_transcript(
    transcript_text: str,
    output_path: Path | None = None,
    output_filename: str | None = None,
) -> Path:
    logger.info("Starting transcript summarization.")

    if output_path is None:
        if output_filename is None:
            raise ValueError("Either output_path or output_filename must be provided.")

        output_path = SUMMARY_OUTPUT_DIR / output_filename

    cleaned_text = clean_transcript_text(transcript_text)

    important_sentences = select_important_sentences(
        text=cleaned_text,
        max_sentences=12,
    )

    clean_points = build_model_input(important_sentences)

    if not clean_points:
        logger.warning("No strong lecture points found. Using extractive fallback.")
        final_summary = build_extractive_fallback(
            important_sentences=important_sentences,
            max_words=MAX_SUMMARY_WORDS,
        )
    else:
        try:
            tokenizer, model = load_summarization_model()

            model_summary = generate_summary_with_model(
                clean_points=clean_points,
                tokenizer=tokenizer,
                model=model,
            )

            final_summary = clean_summary(model_summary)
            final_summary = limit_summary_words(final_summary)

            if not is_summary_usable(final_summary, important_sentences):
                logger.warning("Model summary was weak or leaked prompt text. Using extractive fallback.")
                final_summary = build_extractive_fallback(
                    important_sentences=important_sentences,
                    max_words=MAX_SUMMARY_WORDS,
                )
        except Exception as error:
            logger.warning(
                "FLAN-T5 summarization failed: %s. Using deterministic fallback summary.",
                error,
            )
            final_summary = build_extractive_fallback(
                important_sentences=important_sentences,
                max_words=MAX_SUMMARY_WORDS,
            )

    final_summary = clean_summary(final_summary)
    final_summary = limit_summary_words(final_summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_summary, encoding="utf-8")

    logger.info("Summary saved to: %s", output_path)

    return output_path
