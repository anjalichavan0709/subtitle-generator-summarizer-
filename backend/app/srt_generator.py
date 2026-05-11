from pathlib import Path

from app.config import SUBTITLE_OUTPUT_DIR, create_required_directories
from app.logger import get_logger


logger = get_logger(__name__)


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds into SRT timestamp format.

    Example:
    65.35 seconds → 00:01:05,350
    """

    milliseconds = int((seconds - int(seconds)) * 1000)
    total_seconds = int(seconds)

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{secs:02},{milliseconds:03}"


def generate_srt_from_segments(
    segments: list[dict],
    output_filename: str,
) -> Path:
    """
    Generate a .srt subtitle file from Whisper timestamp segments.

    Args:
        segments: Whisper segments containing start, end, and text.
        output_filename: Name for the subtitle file.

    Returns:
        Path to the generated .srt file.
    """

    create_required_directories()

    if not segments:
        raise ValueError("No transcription segments found for SRT generation.")

    output_path = SUBTITLE_OUTPUT_DIR / output_filename

    if output_path.suffix.lower() != ".srt":
        output_path = output_path.with_suffix(".srt")

    logger.info(f"Generating SRT file: {output_path.name}")

    try:
        with open(output_path, "w", encoding="utf-8") as file:
            for index, segment in enumerate(segments, start=1):
                start_time = format_timestamp(float(segment["start"]))
                end_time = format_timestamp(float(segment["end"]))
                text = segment["text"].strip()

                file.write(f"{index}\n")
                file.write(f"{start_time} --> {end_time}\n")
                file.write(f"{text}\n\n")

        logger.info(f"SRT file generated successfully: {output_path}")

        return output_path

    except Exception as error:
        logger.error(f"SRT generation failed: {error}")
        raise