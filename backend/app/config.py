from pathlib import Path


# ============================================================
# Project paths
# ============================================================

BACKEND_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BACKEND_DIR / "data"
RAW_VIDEOS_DIR = DATA_DIR / "raw_videos"
REFERENCE_TRANSCRIPTS_DIR = DATA_DIR / "reference_transcripts"
REFERENCE_SUMMARIES_DIR = DATA_DIR / "reference_summaries"

OUTPUT_DIR = BACKEND_DIR / "outputs"
AUDIO_OUTPUT_DIR = OUTPUT_DIR / "audio"
TRANSCRIPT_OUTPUT_DIR = OUTPUT_DIR / "transcripts"
SUBTITLE_OUTPUT_DIR = OUTPUT_DIR / "subtitles"
SUMMARY_OUTPUT_DIR = OUTPUT_DIR / "summaries"
EVALUATION_OUTPUT_DIR = OUTPUT_DIR / "evaluation"

LOGS_DIR = BACKEND_DIR / "logs"


# ============================================================
# Model configuration
# ============================================================

WHISPER_MODEL_NAME = "base"

# NewtonAI requirement allows BART or FLAN-T5.
# We use FLAN-T5 because it is instruction-following and suitable for
# concise educational summaries.
SUMMARIZATION_MODEL_NAME = "google/flan-t5-base"


# ============================================================
# Processing configuration
# ============================================================

SUPPORTED_VIDEO_FORMATS = {".mp4", ".mov", ".mkv", ".avi"}

MAX_SUMMARY_WORDS = 100


def create_required_directories() -> None:
    """
    Create all required input, output, and log folders.

    This allows the project to regenerate folders even if outputs/logs were deleted.
    """

    required_directories = [
        DATA_DIR,
        RAW_VIDEOS_DIR,
        REFERENCE_TRANSCRIPTS_DIR,
        REFERENCE_SUMMARIES_DIR,
        OUTPUT_DIR,
        AUDIO_OUTPUT_DIR,
        TRANSCRIPT_OUTPUT_DIR,
        SUBTITLE_OUTPUT_DIR,
        SUMMARY_OUTPUT_DIR,
        EVALUATION_OUTPUT_DIR,
        LOGS_DIR,
    ]

    for directory in required_directories:
        directory.mkdir(parents=True, exist_ok=True)