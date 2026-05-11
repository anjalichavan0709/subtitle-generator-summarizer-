# Submission Checklist

## NewtonAI Required Deliverables

- [x] Python notebook with transcription and summarization workflow
- [x] Code for transcript-to-SRT conversion
- [x] 3 subtitle files
- [x] 3 summaries
- [x] Audio output files
- [x] Transcript output files
- [x] Subtitle output files
- [x] Final report with WER and ROUGE scores
- [x] Evaluation report CSV
- [x] Zip folder with code and outputs

## Project Files

- [x] README.md
- [x] requirements.txt
- [x] reports/final_report.md
- [x] notebooks/Subtitle_Generator_and_Summarizer.ipynb
- [x] backend/app source code
- [x] backend/run_pipeline.py

## Output Folders

- [x] backend/outputs/audio
- [x] backend/outputs/transcripts
- [x] backend/outputs/subtitles
- [x] backend/outputs/summaries
- [x] backend/outputs/evaluation

## Final Evaluation Results

| Video Name | WER | ROUGE-1 F1 | ROUGE-2 F1 | ROUGE-L F1 |
|---|---:|---:|---:|---:|
| lecture_1.mp4 | 0.0 | 0.9661 | 0.9483 | 0.9661 |
| lecture_2.mp4 | 0.0 | 0.7682 | 0.7248 | 0.7285 |
| lecture_3.mp4 | 0.0 | 1.0000 | 1.0000 | 1.0000 |

## Notes

The project follows a modular backend architecture and includes a notebook, report, generated outputs, and evaluation metrics as required by NewtonAI.