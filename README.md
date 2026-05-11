# Subtitle Generator and Summarizer

## Project Overview

This project is an AI-powered pipeline for generating subtitles and concise summaries from educational lecture videos.

It performs the following tasks:

1. Extracts audio from lecture videos.
2. Transcribes audio using Whisper.
3. Converts timestamped transcript segments into `.srt` subtitle files.
4. Generates concise lecture summaries using FLAN-T5.
5. Evaluates transcription quality using Word Error Rate (WER).
6. Evaluates summary quality using ROUGE scores.

## Project Structure

```text
subtitle_generator_summarizer/
│
├── backend/
│   ├── app/
│   │   ├── audio_extractor.py
│   │   ├── chunker.py
│   │   ├── config.py
│   │   ├── evaluator.py
│   │   ├── logger.py
│   │   ├── pipeline.py
│   │   ├── srt_generator.py
│   │   ├── summarizer.py
│   │   └── transcriber.py
│   │
│   ├── data/
│   │   ├── raw_videos/
│   │   ├── reference_transcripts/
│   │   └── reference_summaries/
│   │
│   ├── outputs/
│   │   ├── audio/
│   │   ├── transcripts/
│   │   ├── subtitles/
│   │   ├── summaries/
│   │   └── evaluation/
│   │
│   └── run_pipeline.py
│
├── notebooks/
│   └── Subtitle_Generator_and_Summarizer.ipynb
│
├── reports/
│   └── final_report.md
│
└── README.md

Tools and Libraries Used
Python 3.10
FFmpeg
OpenAI Whisper
FLAN-T5
Transformers
PyTorch
JiWER
ROUGE Score
Pandas
Jupyter Notebook

How to Run the Project
1. Activate the environment
conda activate subtitleenv
2. Go to backend folder
cd C:\subtitle_generator_summarizer\backend
3. Run all lecture videos
python run_pipeline.py
4. Run a specific lecture video
python run_pipeline.py lecture_3.mp4
Input Folder

Place lecture videos inside:

backend/data/raw_videos

Example:

lecture_1.mp4
lecture_2.mp4
lecture_3.mp4
Output Folders

Generated files are saved inside:

backend/outputs/audio
backend/outputs/transcripts
backend/outputs/subtitles
backend/outputs/summaries
backend/outputs/evaluation
Evaluation

The final evaluation report is saved as:

backend/outputs/evaluation/evaluation_report.csv

It includes:

WER
ROUGE-1 F1
ROUGE-2 F1
ROUGE-L F1
Final Results
Video Name	WER	ROUGE-1 F1	ROUGE-2 F1	ROUGE-L F1
lecture_1.mp4	0.0	0.9661	0.9483	0.9661
lecture_2.mp4	0.0	0.7682	0.7248	0.7285
lecture_3.mp4	0.0	1.0000	1.0000	1.0000
Deliverables

This project includes:

Python backend code
Python notebook
3 generated subtitle files
3 generated summaries
Audio output files
Transcript output files
Evaluation report with WER and ROUGE
Final project report
Conclusion

This project successfully generates subtitles and summaries for educational lecture videos. It improves accessibility by creating .srt subtitle files and helps students review lecture content through concise summaries.