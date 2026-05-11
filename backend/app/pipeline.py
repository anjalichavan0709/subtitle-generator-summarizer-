from pathlib import Path

from app.audio_extractor import extract_audio_from_video
from app.transcriber import transcribe_audio
from app.srt_generator import generate_srt_from_segments
from app.summarizer import summarize_transcript
from app.evaluator import evaluate_outputs
from app.config import (
    TRANSCRIPT_OUTPUT_DIR,
    REFERENCE_TRANSCRIPTS_DIR,
    REFERENCE_SUMMARIES_DIR,
    create_required_directories,
)
from app.logger import get_logger


logger = get_logger(__name__)


def save_transcript(transcript_text: str, output_path: Path) -> Path:
    """
    Save generated transcript text to a .txt file.
    """

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(transcript_text, encoding="utf-8")

    return output_path


def process_single_video(video_path: str | Path) -> dict:
    """
    Run the full backend pipeline for one educational or tutorial video.

    Steps:
    1. Extract audio from video
    2. Transcribe audio with Whisper
    3. Save transcript text
    4. Generate SRT subtitles
    5. Generate summary
    6. Evaluate outputs if reference files are available
    """

    create_required_directories()

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    output_stem = video_path.stem

    transcript_path = TRANSCRIPT_OUTPUT_DIR / f"{output_stem}_transcript.txt"
    subtitle_filename = f"{output_stem}.srt"
    summary_filename = f"{output_stem}_summary.txt"

    reference_transcript_path = (
        REFERENCE_TRANSCRIPTS_DIR / f"{output_stem}_reference_transcript.txt"
    )
    reference_summary_path = (
        REFERENCE_SUMMARIES_DIR / f"{output_stem}_reference_summary.txt"
    )

    logger.info(f"Starting pipeline for: {video_path.name}")

    audio_path = extract_audio_from_video(video_path)

    transcription_result = transcribe_audio(audio_path)
    transcript_text = transcription_result.get("text", "").strip()
    segments = transcription_result.get("segments", [])

    if not transcript_text:
        raise ValueError(f"No transcript text generated for: {video_path.name}")

    transcript_path = save_transcript(
        transcript_text=transcript_text,
        output_path=transcript_path,
    )

    subtitle_path = generate_srt_from_segments(
        segments=segments,
        output_filename=subtitle_filename,
    )

    summary_path = summarize_transcript(
        transcript_text=transcript_text,
        output_filename=summary_filename,
    )

    evaluation_result = evaluate_outputs(
        video_name=video_path.name,
        reference_transcript_path=reference_transcript_path,
        generated_transcript_path=transcript_path,
        reference_summary_path=reference_summary_path,
        generated_summary_path=summary_path,
    )

    logger.info(f"Pipeline completed successfully for: {video_path.name}")

    return {
        "video_name": video_path.name,
        "audio_path": str(audio_path),
        "transcript_path": str(transcript_path),
        "subtitle_path": str(subtitle_path),
        "summary_path": str(summary_path),
        "evaluation": evaluation_result,
    }