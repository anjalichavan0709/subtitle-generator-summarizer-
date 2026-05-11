from pathlib import Path
import subprocess

from app.config import AUDIO_OUTPUT_DIR, SUPPORTED_VIDEO_FORMATS, create_required_directories
from app.logger import get_logger


logger = get_logger(__name__)


def extract_audio_from_video(video_path: str | Path) -> Path:
    """
    Extract audio from a lecture video and save it as a .wav file using FFmpeg.

    Why FFmpeg?
    FFmpeg is more reliable than MoviePy for production pipelines because it can
    handle videos with multiple streams such as video, audio, subtitles, and cover images.

    Args:
        video_path: Path to the input lecture video.

    Returns:
        Path to the extracted .wav audio file.
    """

    create_required_directories()

    video_path = Path(video_path)

    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    if video_path.suffix.lower() not in SUPPORTED_VIDEO_FORMATS:
        raise ValueError(
            f"Unsupported video format: {video_path.suffix}. "
            f"Supported formats: {SUPPORTED_VIDEO_FORMATS}"
        )

    output_audio_path = AUDIO_OUTPUT_DIR / f"{video_path.stem}.wav"

    logger.info(f"Starting audio extraction for: {video_path.name}")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "pcm_s16le",
        "-ar",
        "16000",
        "-ac",
        "1",
        str(output_audio_path),
    ]

    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        logger.info(f"Audio extracted successfully: {output_audio_path}")

        return output_audio_path

    except subprocess.CalledProcessError as error:
        logger.error(f"Audio extraction failed for {video_path.name}")
        logger.error(error.stderr)
        raise RuntimeError(
            f"FFmpeg failed while extracting audio from {video_path.name}"
        ) from error