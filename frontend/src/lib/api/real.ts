import type { ContentAnalysis } from "@/types/analysis"

// Where the FastAPI server lives. Hardcoded for development.
// In production, this would come from an environment variable.
const API_BASE = "http://localhost:8000"

// What our backend returns from POST /analyze.
// This shape is defined by FastAPI's AnalyzeResponse model.
type AnalyzeResponse = {
  analysis: ContentAnalysis
  pdf_id: string
}

// The two valid input shapes — same tagged union the mock used.
type AnalyzeInput =
  | { kind: "file"; files: File[] }
  | { kind: "text"; text: string }

/**
 * Send content to the backend and get back the analysis + a pdf_id.
 *
 * The signature is identical to the mock except it now returns the
 * pdf_id too, so the caller can build a download link.
 */
export async function analyzeContent(
  input: AnalyzeInput,
): Promise<AnalyzeResponse> {
  // FormData is how browsers send multipart/form-data — the format
  // FastAPI's UploadFile and Form() expect.
  const formData = new FormData()

  if (input.kind === "file") {
    // Each file gets appended under the same field name "files".
    // FastAPI receives them as list[UploadFile].
    for (const file of input.files) {
      formData.append("files", file)
    }
  } else {
    formData.append("text", input.text)
  }

  const response = await fetch(`${API_BASE}/analyze`, {
    method: "POST",
    body: formData,
    // NOTE: do NOT set Content-Type manually. The browser sets it correctly
    // (with the boundary string) when you pass FormData. Setting it yourself
    // breaks the upload.
  })

  if (!response.ok) {
    // FastAPI sends errors as { "detail": "message" }
    const errorBody = await response.json().catch(() => ({}))
    throw new Error(errorBody.detail || `Server error: ${response.status}`)
  }

  return response.json()
}

/**
 * Build the URL to download the PDF for a given pdf_id.
 * The actual download is triggered by setting window.location or
 * by an <a href={pdfUrl} download>...</a>.
 */
export function getPdfUrl(pdfId: string): string {
  return `${API_BASE}/pdf/${pdfId}`
}
import type { JobSummary, JobDetail } from "@/types/analysis"

export async function listJobs(): Promise<JobSummary[]> {
  const response = await fetch(`${API_BASE}/jobs`)
  if (!response.ok) {
    throw new Error(`Failed to load jobs: ${response.status}`)
  }
  return response.json()
}

export async function getJob(jobId: string): Promise<JobDetail> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`)
  if (!response.ok) {
    throw new Error(`Failed to load job: ${response.status}`)
  }
  return response.json()
}