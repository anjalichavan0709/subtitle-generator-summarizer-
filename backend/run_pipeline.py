from pathlib import Path
import sys
import pandas as pd

from app.config import RAW_VIDEOS_DIR, EVALUATION_OUTPUT_DIR, create_required_directories
from app.pipeline import process_single_video
from app.evaluator import save_evaluation_report
from app.logger import get_logger


logger = get_logger(__name__)


def get_video_files_from_arguments() -> list[Path]:
    """
    Get video files to process.

    Usage:
    - python run_pipeline.py
      Processes all videos in backend/data/raw_videos/

    - python run_pipeline.py lecture_3.mp4
      Processes only lecture_3.mp4
    """

    create_required_directories()

    if len(sys.argv) > 1:
        video_name = sys.argv[1]
        video_path = RAW_VIDEOS_DIR / video_name

        if not video_path.exists():
            raise FileNotFoundError(f"Video not found: {video_path}")

        return [video_path]

    video_files = []

    for extension in ["*.mp4", "*.mov", "*.mkv", "*.avi"]:
        video_files.extend(RAW_VIDEOS_DIR.glob(extension))

    return video_files


def update_evaluation_report(new_results: list[dict]) -> Path:
    """
    Update evaluation_report.csv without losing previous lecture results.

    If lecture_1 and lecture_2 already exist in the CSV, and we process only
    lecture_3, this function keeps old rows and adds/updates lecture_3.
    """

    output_path = EVALUATION_OUTPUT_DIR / "evaluation_report.csv"

    new_dataframe = pd.DataFrame(new_results)

    if output_path.exists():
        old_dataframe = pd.read_csv(output_path)

        combined_dataframe = pd.concat(
            [old_dataframe, new_dataframe],
            ignore_index=True,
        )

        combined_dataframe = combined_dataframe.drop_duplicates(
            subset=["video_name"],
            keep="last",
        )
    else:
        combined_dataframe = new_dataframe

    combined_dataframe.to_csv(output_path, index=False)

    logger.info(f"Evaluation report updated successfully: {output_path}")

    return output_path


def main():
    """
    Main runner for processing lecture videos.
    """

    create_required_directories()

    try:
        video_files = get_video_files_from_arguments()
    except Exception as error:
        logger.error(error)
        print(error)
        return

    if not video_files:
        logger.warning(f"No video files found in: {RAW_VIDEOS_DIR}")
        print("\nNo videos found.")
        print("Please add your lecture videos inside:")
        print(RAW_VIDEOS_DIR)
        return

    all_evaluation_results = []

    for video_path in video_files:
        try:
            result = process_single_video(video_path)
            all_evaluation_results.append(result["evaluation"])

            print("\nProcessing completed for:", result["video_name"])
            print("Audio:", result["audio_path"])
            print("Transcript:", result["transcript_path"])
            print("Subtitle:", result["subtitle_path"])
            print("Summary:", result["summary_path"])
            print("Evaluation:", result["evaluation"])

        except Exception as error:
            logger.error(f"Failed to process {video_path.name}: {error}")
            print(f"\nFailed to process {video_path.name}: {error}")

    if all_evaluation_results:
        report_path = update_evaluation_report(all_evaluation_results)
        print("\nEvaluation report updated at:")
        print(report_path)


if __name__ == "__main__":
    main()