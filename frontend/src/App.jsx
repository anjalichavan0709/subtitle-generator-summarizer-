import { useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/process-video";

function App() {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [showMoreTranscript, setShowMoreTranscript] = useState(false);

  const handleFileChange = (event) => {
    const file = event.target.files[0];

    setSelectedFile(file);
    setResult(null);
    setErrorMessage("");
    setShowMoreTranscript(false);
  };

  const formatMetric = (value) => {
    if (value === null || value === undefined || value === "") {
      return "Reference not available";
    }

    if (typeof value === "number") {
      return value.toFixed(4);
    }

    return value;
  };

  const copyToClipboard = async (text, label) => {
    if (!text) {
      return;
    }

    try {
      await navigator.clipboard.writeText(text);
      alert(`${label} copied to clipboard.`);
    } catch {
      alert(`Could not copy ${label}.`);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setErrorMessage("Please select a lecture video first.");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);

    setIsProcessing(true);
    setErrorMessage("");
    setResult(null);
    setShowMoreTranscript(false);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Something went wrong while processing the video."
        );
      }

      setResult(data);
    } catch (error) {
      setErrorMessage(error.message);
    } finally {
      setIsProcessing(false);
    }
  };

  const transcriptPreview = result?.preview?.transcript_preview || "";
  const visibleTranscript = showMoreTranscript
    ? transcriptPreview
    : transcriptPreview.slice(0, 1400);

  return (
    <main className="appShell">
      <section className="hero">
        <div className="heroBadge">AI Lecture Processing Tool</div>
        <h1>Subtitle Generator & Summarizer</h1>
        <p>
          Upload a lecture video and generate a transcript, SRT subtitle file,
          concise summary, and evaluation-ready outputs through a real AI
          pipeline.
        </p>
      </section>

      <section className="toolGrid">
        <section className="panel uploadPanel">
          <div className="panelHeader">
            <span className="stepBadge">01</span>
            <div>
              <p className="panelLabel">Upload</p>
              <h2>Lecture Video</h2>
            </div>
          </div>

          <p className="helperText">
            Choose a lecture/tutorial video. Supported formats are MP4, MOV,
            MKV, and AVI.
          </p>

          <div className="uploadBox">
            <input
              type="file"
              accept=".mp4,.mov,.mkv,.avi"
              onChange={handleFileChange}
            />

            <div className="selectedFile">
              <span>Selected file</span>
              <strong>
                {selectedFile ? selectedFile.name : "No file selected yet"}
              </strong>
            </div>

            <button
              className="primaryButton"
              onClick={handleUpload}
              disabled={isProcessing}
            >
              {isProcessing ? "Processing..." : "Process Video"}
            </button>
          </div>

          {errorMessage && <div className="errorBox">{errorMessage}</div>}
        </section>

        <section className="panel statusPanel">
          <div className="panelHeader">
            <span className="stepBadge">02</span>
            <div>
              <p className="panelLabel">Status</p>
              <h2>Processing Pipeline</h2>
            </div>
          </div>

          <div className="statusList">
            <div className={isProcessing ? "statusItem active" : "statusItem"}>
              <span>Audio extraction</span>
              <strong>{isProcessing ? "Running" : result ? "Done" : "Ready"}</strong>
            </div>

            <div className={isProcessing ? "statusItem active" : "statusItem"}>
              <span>Whisper transcription</span>
              <strong>{isProcessing ? "Running" : result ? "Done" : "Ready"}</strong>
            </div>

            <div className={isProcessing ? "statusItem active" : "statusItem"}>
              <span>SRT subtitle generation</span>
              <strong>{isProcessing ? "Running" : result ? "Done" : "Ready"}</strong>
            </div>

            <div className={isProcessing ? "statusItem active" : "statusItem"}>
              <span>Summary + evaluation</span>
              <strong>{isProcessing ? "Running" : result ? "Done" : "Ready"}</strong>
            </div>
          </div>

          <p className="smallNote">
            Processing time depends on the length of the uploaded video.
          </p>
        </section>
      </section>

      {result && (
        <section className="resultStack">
          <section className="panel summaryPanel">
            <div className="panelHeader">
              <span className="stepBadge">03</span>
              <div>
                <p className="panelLabel">Output</p>
                <h2>Generated Summary</h2>
              </div>
            </div>

            <p className="summaryText">
              {result.preview.summary || "Summary not available."}
            </p>

            <button
              className="ghostButton"
              onClick={() =>
                copyToClipboard(result.preview.summary, "Summary")
              }
            >
              Copy Summary
            </button>
          </section>

          <section className="twoColumn">
            <section className="panel">
              <div className="panelHeader">
                <span className="stepBadge">04</span>
                <div>
                  <p className="panelLabel">Preview</p>
                  <h2>Transcript Preview</h2>
                </div>
              </div>

              <p className="smallNote">
                {result.notes?.transcript_preview_note ||
                  "This is a preview. The full transcript is saved in the output folder."}
              </p>

              <pre className="previewBox">
                {visibleTranscript ||
                  "Transcript preview unavailable."}
              </pre>

              <div className="buttonRow">
                {transcriptPreview.length > 1400 && (
                  <button
                    className="ghostButton"
                    onClick={() => setShowMoreTranscript(!showMoreTranscript)}
                  >
                    {showMoreTranscript ? "Show Less" : "Show More"}
                  </button>
                )}

                <button
                  className="ghostButton"
                  onClick={() =>
                    copyToClipboard(transcriptPreview, "Transcript preview")
                  }
                >
                  Copy Transcript Preview
                </button>
              </div>
            </section>

            <section className="panel">
              <div className="panelHeader">
                <span className="stepBadge">05</span>
                <div>
                  <p className="panelLabel">Accessibility</p>
                  <h2>SRT Subtitle Preview</h2>
                </div>
              </div>

              <p className="smallNote">
                {result.notes?.subtitle_preview_note ||
                  "This is a preview. The full SRT file is saved in the output folder."}
              </p>

              <pre className="previewBox">
                {result.preview.subtitle_preview ||
                  "Subtitle preview unavailable."}
              </pre>

              <button
                className="ghostButton"
                onClick={() =>
                  copyToClipboard(
                    result.preview.subtitle_preview,
                    "Subtitle preview"
                  )
                }
              >
                Copy SRT Preview
              </button>
            </section>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <span className="stepBadge">06</span>
              <div>
                <p className="panelLabel">Evaluation</p>
                <h2>WER & ROUGE Metrics</h2>
              </div>
            </div>

            <p className="smallNote">
              {result.notes?.evaluation_note ||
                "WER and ROUGE are available only when matching reference files exist."}
            </p>

            <div className="metricsGrid">
              <div className="metricCard">
                <span>WER</span>
                <strong>{formatMetric(result.evaluation.wer)}</strong>
              </div>
              <div className="metricCard">
                <span>ROUGE-1 F1</span>
                <strong>{formatMetric(result.evaluation.rouge1_f1)}</strong>
              </div>
              <div className="metricCard">
                <span>ROUGE-2 F1</span>
                <strong>{formatMetric(result.evaluation.rouge2_f1)}</strong>
              </div>
              <div className="metricCard">
                <span>ROUGE-L F1</span>
                <strong>{formatMetric(result.evaluation.rougeL_f1)}</strong>
              </div>
            </div>
          </section>

          <section className="panel">
            <div className="panelHeader">
              <span className="stepBadge">07</span>
              <div>
                <p className="panelLabel">Files</p>
                <h2>Generated Output Files</h2>
              </div>
            </div>

            <div className="outputGrid">
              <div>
                <span>Uploaded video</span>
                <p>{result.outputs.video_path}</p>
              </div>
              <div>
                <span>Audio</span>
                <p>{result.outputs.audio_path}</p>
              </div>
              <div>
                <span>Transcript</span>
                <p>{result.outputs.transcript_path}</p>
              </div>
              <div>
                <span>Subtitle</span>
                <p>{result.outputs.subtitle_path}</p>
              </div>
              <div>
                <span>Summary</span>
                <p>{result.outputs.summary_path}</p>
              </div>
              <div>
                <span>Evaluation report</span>
                <p>{result.outputs.evaluation_report_path}</p>
              </div>
            </div>
          </section>
        </section>
      )}
    </main>
  );
}

export default App;