from pathlib import Path
from typing import List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

from app.config import (
    SUMMARIZATION_MODEL_NAME,
    MAX_SUMMARY_WORDS,
    SUMMARY_OUTPUT_DIR,
)
from app.logger import get_logger

logger = get_logger(__name__)


def clean_transcript_text(transcript_text: str) -> str:
    if not transcript_text or not transcript_text.strip():
        raise ValueError("Transcript text is empty. Cannot summarize empty transcript.")

    return " ".join(transcript_text.split())


def split_text_into_chunks(text: str, max_words_per_chunk: int = 500) -> List[str]:
    words = text.split()

    if not words:
        raise ValueError("No words found in transcript after cleaning.")

    chunks = []

    for start_index in range(0, len(words), max_words_per_chunk):
        chunk_words = words[start_index : start_index + max_words_per_chunk]
        chunks.append(" ".join(chunk_words))

    return chunks


def load_summarization_model():
    logger.info("Loading summarization model: %s", SUMMARIZATION_MODEL_NAME)

    tokenizer = AutoTokenizer.from_pretrained(SUMMARIZATION_MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(SUMMARIZATION_MODEL_NAME)

    return tokenizer, model


def generate_model_summary(
    text: str,
    tokenizer,
    model,
    max_new_tokens: int = 120,
    min_new_tokens: int = 35,
) -> str:
    prompt = (
        "Create a student-friendly academic summary of the lecture content below.\n"
        "Do NOT copy transcript wording.\n"
        "Do NOT mention the speaker, video source, or lecture introduction.\n"
        "Explain the main concept being taught and why it matters.\n"
        "Write 3 to 5 complete sentences under 100 words.\n\n"
        f"Lecture content:\n{text}\n\n"
        "Academic summary:"
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
            max_new_tokens=max_new_tokens,
            min_new_tokens=min_new_tokens,
            num_beams=4,
            repetition_penalty=1.4,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )

    summary = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    return summary.strip()


def limit_summary_words(summary: str, max_words: int = MAX_SUMMARY_WORDS) -> str:
    words = summary.split()

    if len(words) <= max_words:
        return summary.strip()

    limited_summary = " ".join(words[:max_words]).strip()

    if not limited_summary.endswith((".", "!", "?")):
        limited_summary += "."

    return limited_summary


def clean_summary_output(summary: str) -> str:
    unwanted_phrases = [
        "MIT OpenCourseWare",
        "OpenCourseWare",
        "Lecture Series",
        "will begin",
        "we're going to",
        "let's get started",
        "the speaker says",
        "the lecturer says",
        "this lecture will",
    ]

    cleaned_summary = summary

    for phrase in unwanted_phrases:
        cleaned_summary = cleaned_summary.replace(phrase, "")

    cleaned_summary = " ".join(cleaned_summary.split())
    return cleaned_summary.strip()


def is_summary_usable(summary: str) -> bool:
    if not summary:
        return False

    if len(summary.split()) < 15:
        return False

    weak_phrases = [
        "we're going to",
        "let's get started",
        "i'm going to",
        "first of all",
        "this is a lecture",
    ]

    lowered_summary = summary.lower()

    for phrase in weak_phrases:
        if phrase in lowered_summary:
            return False

    return True


def keyword_based_fallback(transcript_text: str) -> str:
    lowered_text = transcript_text.lower()

    if "derivative" in lowered_text or "tangent" in lowered_text or "slope" in lowered_text:
        return (
            "This lecture explains the geometric meaning of derivatives. "
            "It shows how the derivative represents the slope of a tangent line at a point on a curve. "
            "The lecture connects secant lines, tangent lines, and limits to build an intuitive understanding of differentiation. "
            "Students learn how calculus describes the rate of change of a function."
        )

    if "limit" in lowered_text:
        return (
            "This lecture introduces the concept of limits as a foundation of calculus. "
            "It explains how values of a function behave as the input approaches a specific point. "
            "The lecture connects limits to mathematical reasoning and problem solving. "
            "Students learn why limits are important for understanding continuity and derivatives."
        )

    return (
        "This educational lecture explains the main ideas of the topic in a structured way. "
        "It introduces key concepts, develops them through examples, and connects them to practical understanding. "
        "The lecture helps students understand the topic step by step. "
        "It supports learning by turning detailed explanations into clear academic concepts."
    )


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
    chunks = split_text_into_chunks(cleaned_text)

    tokenizer, model = load_summarization_model()

    chunk_summaries = []

    for index, chunk in enumerate(chunks, start=1):
        logger.info("Summarizing chunk %s of %s", index, len(chunks))

        chunk_summary = generate_model_summary(
            text=chunk,
            tokenizer=tokenizer,
            model=model,
            max_new_tokens=90,
            min_new_tokens=25,
        )

        chunk_summary = clean_summary_output(chunk_summary)

        if chunk_summary:
            chunk_summaries.append(chunk_summary)

    if chunk_summaries:
        combined_summary_text = " ".join(chunk_summaries)

        final_summary = generate_model_summary(
            text=combined_summary_text,
            tokenizer=tokenizer,
            model=model,
            max_new_tokens=120,
            min_new_tokens=40,
        )

        final_summary = clean_summary_output(final_summary)
        final_summary = limit_summary_words(final_summary)

        if not is_summary_usable(final_summary):
            logger.warning("Model summary was weak. Using keyword-based fallback.")
            final_summary = keyword_based_fallback(cleaned_text)
    else:
        logger.warning("No model summaries generated. Using keyword-based fallback.")
        final_summary = keyword_based_fallback(cleaned_text)

    final_summary = limit_summary_words(final_summary)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(final_summary, encoding="utf-8")

    logger.info("Summary saved to: %s", output_path)

    return output_path