from pathlib import Path
import shutil
import uuid

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    RAW_VIDEOS_DIR,
    AUDIO_OUTPUT_DIR,
    TRANSCRIPT_OUTPUT_DIR,
    SUBTITLE_OUTPUT_DIR,
    SUMMARY_OUTPUT_DIR,
    EVALUATION_OUTPUT_DIR,
    create_required_directories,
)
from app.pipeline import process_single_video
from app.evaluator import save_evaluation_report


app = FastAPI(
    title="Subtitle Generator and Summarizer API",
    description=(
        "Upload lecture videos and generate transcripts, subtitles, summaries, "
        "and evaluation outputs."
    ),
    version="1.0.0",
)


# Allows the React frontend to call this FastAPI backend locally.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".mkv", ".avi"}


def clean_preview_text(text: str) -> str:
    """
    Clean transcript preview text for frontend display.

    This removes common source/license text and extra spacing so the preview
    starts closer to the actual lecture content.
    """

    if not text:
        return ""

    removable_phrases = [
        "The following content is provided under a Creative Commons license.",
        "Your support will help MIT OpenCourseWare continue to offer high quality educational resources for free.",
        "To make a donation or to view additional materials from hundreds of MIT courses, visit MIT OpenCourseWare at ocw.mit.edu.",
    ]

    cleaned_text = text

    for phrase in removable_phrases:
        cleaned_text = cleaned_text.replace(phrase, "")

    cleaned_text = " ".join(cleaned_text.split())

    return cleaned_text.strip()


@app.get("/")
def health_check():
    """
    Simple health check endpoint.
    """

    return {
        "status": "running",
        "message": "Subtitle Generator and Summarizer API is running.",
    }


@app.post("/process-video")
async def process_uploaded_video(file: UploadFile = File(...)):
    """
    Upload a lecture video, run the processing pipeline,
    and return generated output details for the React frontend.
    """

    create_required_directories()

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    original_filename = Path(file.filename).name
    file_extension = Path(original_filename).suffix.lower()

    if file_extension not in SUPPORTED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file format. "
                f"Supported formats: {sorted(SUPPORTED_VIDEO_EXTENSIONS)}"
            ),
        )

    safe_stem = Path(original_filename).stem.replace(" ", "_")
    unique_id = uuid.uuid4().hex[:8]
    saved_filename = f"{safe_stem}_{unique_id}{file_extension}"
    saved_video_path = RAW_VIDEOS_DIR / saved_filename

    try:
        # Save uploaded video into backend/data/raw_videos
        with open(saved_video_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Run existing backend pipeline on uploaded video
        result = process_single_video(saved_video_path)

        # Save/update evaluation report for this API-processed video
        save_evaluation_report([result["evaluation"]])

        video_stem = saved_video_path.stem

        audio_path = AUDIO_OUTPUT_DIR / f"{video_stem}.wav"
        transcript_path = TRANSCRIPT_OUTPUT_DIR / f"{video_stem}_transcript.txt"
        subtitle_path = SUBTITLE_OUTPUT_DIR / f"{video_stem}.srt"
        summary_path = SUMMARY_OUTPUT_DIR / f"{video_stem}_summary.txt"
        evaluation_report_path = EVALUATION_OUTPUT_DIR / "evaluation_report.csv"

        transcript_text = (
            transcript_path.read_text(encoding="utf-8")
            if transcript_path.exists()
            else ""
        )

        summary_text = (
            summary_path.read_text(encoding="utf-8")
            if summary_path.exists()
            else ""
        )

        subtitle_text = (
            subtitle_path.read_text(encoding="utf-8")
            if subtitle_path.exists()
            else ""
        )

        cleaned_transcript_preview = clean_preview_text(transcript_text)

        return {
            "status": "success",
            "original_filename": original_filename,
            "saved_filename": saved_filename,
            "outputs": {
                "video_path": str(saved_video_path),
                "audio_path": str(audio_path),
                "transcript_path": str(transcript_path),
                "subtitle_path": str(subtitle_path),
                "summary_path": str(summary_path),
                "evaluation_report_path": str(evaluation_report_path),
            },
            "preview": {
                "summary": summary_text,
                "transcript_preview": cleaned_transcript_preview[:4000],
                "subtitle_preview": subtitle_text[:2500],
            },
            "evaluation": result["evaluation"],
            "notes": {
                "transcript_preview_note": (
                    "This is a preview. The full transcript is saved in the transcript output file."
                ),
                "subtitle_preview_note": (
                    "This is a preview. The full SRT subtitle file is saved in the subtitle output file."
                ),
                "evaluation_note": (
                    "WER and ROUGE are shown when matching reference transcript and summary files are available."
                ),
            },
        }

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process video: {error}",
        ) from error