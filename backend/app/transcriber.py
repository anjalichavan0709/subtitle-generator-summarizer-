from pathlib import Path
import whisper

from app.config import TRANSCRIPT_OUTPUT_DIR, WHISPER_MODEL_NAME, create_required_directories
from app.logger import get_logger


logger = get_logger(__name__)


def transcribe_audio(audio_path: str | Path) -> dict:
    """
    Transcribe an audio file using Whisper.

    Args:
        audio_path: Path to the extracted .wav audio file.

    Returns:
        Whisper transcription result dictionary.
        It includes:
        - text: full transcript
        - segments: timestamped transcript chunks
        - language: detected language
    """

    create_required_directories()

    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    logger.info(f"Loading Whisper model: {WHISPER_MODEL_NAME}")

    model = whisper.load_model(WHISPER_MODEL_NAME)

    logger.info(f"Starting transcription for: {audio_path.name}")

    try:
        result = model.transcribe(str(audio_path), fp16=False)

        transcript_text = result.get("text", "").strip()

        transcript_output_path = TRANSCRIPT_OUTPUT_DIR / f"{audio_path.stem}_transcript.txt"

        with open(transcript_output_path, "w", encoding="utf-8") as file:
            file.write(transcript_text)

        logger.info(f"Transcript saved successfully: {transcript_output_path}")

        return result

    except Exception as error:
        logger.error(f"Transcription failed for {audio_path.name}: {error}")
        raise