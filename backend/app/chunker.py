from app.logger import get_logger


logger = get_logger(__name__)


def chunk_text_by_words(text: str, max_words: int = 450) -> list[str]:
    """
    Split transcript text into smaller chunks.

    Why this is needed:
    Summarization models cannot always process very long transcripts at once.
    So we split the transcript into smaller parts before summarizing.

    Args:
        text: Full transcript text.
        max_words: Maximum number of words per chunk.

    Returns:
        List of transcript chunks.
    """

    if not text or not text.strip():
        raise ValueError("Transcript text is empty. Cannot create chunks.")

    words = text.split()
    chunks = []

    for start_index in range(0, len(words), max_words):
        chunk_words = words[start_index : start_index + max_words]
        chunk_text = " ".join(chunk_words)
        chunks.append(chunk_text)

    logger.info(f"Transcript split into {len(chunks)} chunk(s).")

    return chunks