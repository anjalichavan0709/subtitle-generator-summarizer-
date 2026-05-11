from pathlib import Path
import pandas as pd
from jiwer import wer
from rouge_score import rouge_scorer

from app.config import EVALUATION_OUTPUT_DIR, create_required_directories
from app.logger import get_logger


logger = get_logger(__name__)


def read_text_file(file_path: str | Path) -> str:
    """
    Read text content from a file.
    """

    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    return file_path.read_text(encoding="utf-8").strip()


def calculate_wer(reference_text: str, generated_text: str) -> float:
    """
    Calculate Word Error Rate for transcript quality.

    Lower WER means better transcription.
    """

    if not reference_text.strip():
        raise ValueError("Reference transcript is empty. Cannot calculate WER.")

    return wer(reference_text, generated_text)


def calculate_rouge(reference_summary: str, generated_summary: str) -> dict:
    """
    Calculate ROUGE scores for summary quality.

    ROUGE-1: word overlap
    ROUGE-2: two-word phrase overlap
    ROUGE-L: longest common sequence
    """

    if not reference_summary.strip():
        raise ValueError("Reference summary is empty. Cannot calculate ROUGE.")

    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL"],
        use_stemmer=True,
    )

    scores = scorer.score(reference_summary, generated_summary)

    return {
        "rouge1_f1": scores["rouge1"].fmeasure,
        "rouge2_f1": scores["rouge2"].fmeasure,
        "rougeL_f1": scores["rougeL"].fmeasure,
    }


def evaluate_outputs(
    video_name: str,
    reference_transcript_path: str | Path | None,
    generated_transcript_path: str | Path,
    reference_summary_path: str | Path | None,
    generated_summary_path: str | Path,
) -> dict:
    """
    Evaluate transcript and summary outputs using WER and ROUGE.

    If reference files are not provided, metrics are marked as None.
    """

    create_required_directories()

    generated_transcript = read_text_file(generated_transcript_path)
    generated_summary = read_text_file(generated_summary_path)

    evaluation_result = {
        "video_name": video_name,
        "wer": None,
        "rouge1_f1": None,
        "rouge2_f1": None,
        "rougeL_f1": None,
    }

    if reference_transcript_path and Path(reference_transcript_path).exists():
        reference_transcript = read_text_file(reference_transcript_path)
        evaluation_result["wer"] = calculate_wer(
            reference_transcript,
            generated_transcript,
        )
    else:
        logger.warning(
            f"No reference transcript found for {video_name}. WER skipped."
        )

    if reference_summary_path and Path(reference_summary_path).exists():
        reference_summary = read_text_file(reference_summary_path)
        rouge_scores = calculate_rouge(reference_summary, generated_summary)
        evaluation_result.update(rouge_scores)
    else:
        logger.warning(
            f"No reference summary found for {video_name}. ROUGE skipped."
        )

    return evaluation_result


def save_evaluation_report(results: list[dict]) -> Path:
    """
    Save all evaluation results into a CSV file.
    """

    if not results:
        raise ValueError("No evaluation results found to save.")

    output_path = EVALUATION_OUTPUT_DIR / "evaluation_report.csv"

    dataframe = pd.DataFrame(results)
    dataframe.to_csv(output_path, index=False)

    logger.info(f"Evaluation report saved successfully: {output_path}")

    return output_path