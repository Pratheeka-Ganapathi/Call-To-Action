import { useEffect, useState } from "react"
import { Button } from "@/components/button"
import { Textarea } from "@/components/textarea"
import { Label } from "@/components/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/card"
import { Separator } from "@/components/separator"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/tabs"
import { FileDropZone } from "@/components/FileDropZone"
import {
  analyzeContent,
  getJob,
  getPdfUrl,
  listJobs,
} from "@/lib/api/real"
import type { ContentAnalysis, JobSummary } from "@/types/analysis"

function App() {
  const [files, setFiles] = useState<File[]>([])
  const [pastedText, setPastedText] = useState("")
  const [activeTab, setActiveTab] = useState("file")
  const [isLoading, setIsLoading] = useState(false)
  const [result, setResult] = useState<{
    analysis: ContentAnalysis
    pdf_id: string
  } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [jobs, setJobs] = useState<JobSummary[]>([])

  useEffect(() => {
    listJobs()
      .then(setJobs)
      .catch(() => setJobs([]))
  }, [])

  const canAnalyze =
    activeTab === "file" ? files.length > 0 : pastedText.trim().length > 0

  async function handleAnalyze() {
    setIsLoading(true)
    setError(null)
    setResult(null)
    try {
      const input =
        activeTab === "file" && files.length > 0
          ? ({ kind: "file" as const, files })
          : ({ kind: "text" as const, text: pastedText })
      const response = await analyzeContent(input)
      setResult(response)
      const updated = await listJobs()
      setJobs(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Something went wrong.")
    } finally {
      setIsLoading(false)
    }
  }

  async function handleSelectJob(jobId: string) {
    setIsLoading(true)
    setError(null)
    setResult(null)
    try {
      const job = await getJob(jobId)
      setResult({ analysis: job.analysis, pdf_id: job.id })
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load job.")
    } finally {
      setIsLoading(false)
    }
  }

  function handleNewAnalysis() {
    setResult(null)
    setError(null)
    setFiles([])
    setPastedText("")
  }

  function handleDownload() {
    if (!result) return
    window.open(getPdfUrl(result.pdf_id), "_blank")
  }

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-zinc-200 antialiased relative overflow-hidden">
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[400px] bg-violet-500/10 blur-[120px] rounded-full pointer-events-none" />
      <div className="absolute top-40 right-0 w-[400px] h-[400px] bg-cyan-500/5 blur-[100px] rounded-full pointer-events-none" />

      <div className="max-w-3xl mx-auto py-16 px-4 space-y-8 relative">
        <header className="space-y-3">
          <h1 className="text-5xl font-bold tracking-tight bg-gradient-to-r from-zinc-50 via-zinc-100 to-zinc-400 bg-clip-text text-transparent">
            CallToAction
          </h1>
          <div className="flex items-center gap-2">
            <div className="h-1 w-1 rounded-full bg-violet-400" />
            <span className="text-sm text-zinc-400 tracking-wide">
              Read less. Act more.
            </span>
          </div>
          <p className="text-zinc-500 max-w-xl text-[15px] leading-relaxed pt-1">
            Drop in an article or paste text. Get a sharp summary plus
            concrete actions you can take this week.
          </p>
        </header>

        {!result && (
          <Card className="border-zinc-800/80 bg-zinc-950/80 backdrop-blur shadow-2xl shadow-violet-500/5">
            <CardHeader className="pb-3">
              <span className="text-xs uppercase tracking-widest text-violet-400/80 font-medium">
                Input
              </span>
            </CardHeader>
            <CardContent>
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3 bg-zinc-900/60 border border-zinc-800/80">
                  <TabsTrigger value="file">PDF / Text file</TabsTrigger>
                  <TabsTrigger value="text">Paste text</TabsTrigger>
                  <TabsTrigger value="image" disabled>
                    Image
                  </TabsTrigger>
                </TabsList>

                <TabsContent value="file" className="pt-5">
                  <FileDropZone files={files} onFilesChange={setFiles} />
                </TabsContent>

                <TabsContent value="text" className="space-y-3 pt-5">
                  <Label htmlFor="text-input" className="text-zinc-400 text-xs">
                    Paste your content
                  </Label>
                  <Textarea
                    id="text-input"
                    placeholder="Paste an article, notes, or any text..."
                    rows={10}
                    value={pastedText}
                    onChange={(e) => setPastedText(e.target.value)}
                    className="bg-zinc-900/80 border-zinc-800 text-zinc-100 placeholder:text-zinc-600 resize-none"
                  />
                </TabsContent>

                <TabsContent value="image" className="pt-5">
                  <p className="text-zinc-500 text-sm">
                    Image analysis coming soon.
                  </p>
                </TabsContent>
              </Tabs>

              <Button
                onClick={handleAnalyze}
                disabled={!canAnalyze || isLoading}
                className="mt-5 bg-violet-500 text-white hover:bg-violet-400 disabled:bg-zinc-800 disabled:text-zinc-500 shadow-lg shadow-violet-500/20"
              >
                {isLoading ? "Analyzing..." : "Analyze →"}
              </Button>

              {error && (
                <p className="mt-3 text-sm text-red-400">
                  <span className="font-medium">Error:</span> {error}
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {jobs.length > 0 && (
          <Card className="border-zinc-800/80 bg-zinc-950/80 backdrop-blur">
            <CardHeader className="pb-3 flex-row items-center justify-between">
              <span className="text-xs uppercase tracking-widest text-cyan-400/80 font-medium">
                Recent
              </span>
              {result && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNewAnalysis}
                  className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
                >
                  New analysis
                </Button>
              )}
            </CardHeader>
            <CardContent>
              <ul className="divide-y divide-zinc-800">
                {jobs.map((job) => (
                  <li key={job.id}>
                    <button
                      onClick={() => handleSelectJob(job.id)}
                      className="w-full text-left py-3 px-2 rounded hover:bg-zinc-900/60 transition-colors"
                    >
                      <p className="text-sm text-zinc-200 truncate">
                        {job.source_label}
                      </p>
                      <p className="text-xs text-zinc-500 mt-0.5">
                        {new Date(job.created_at).toLocaleString()} ·{" "}
                        {job.source_kind}
                      </p>
                    </button>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {result && (
          <Card className="border-zinc-800/80 bg-zinc-950/80 backdrop-blur shadow-2xl shadow-cyan-500/5">
            <CardHeader className="space-y-4">
              <div className="flex items-start justify-between gap-4">
                <div className="space-y-2">
                  <span className="text-xs uppercase tracking-widest text-cyan-400/80 font-medium">
                    Analysis
                  </span>
                  <CardTitle className="text-2xl font-semibold text-zinc-50 tracking-tight">
                    {result.analysis.metadata.title}
                  </CardTitle>
                </div>
                <Button
                  variant="outline"
                  onClick={handleDownload}
                  className="border-zinc-800 bg-zinc-900 text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
                >
                  Download PDF
                </Button>
              </div>
              <p className="text-lg text-zinc-200 leading-relaxed font-normal">
                {result.analysis.summary.main_point}
              </p>
            </CardHeader>

            <Separator className="bg-zinc-800/80" />

            <CardContent className="space-y-10 pt-6">
              <Section
                label="01"
                title="Key takeaways"
                items={result.analysis.summary.key_takeaways}
                accent="border-zinc-700"
                labelColor="text-zinc-500"
              />

              <div className="space-y-1">
                <span className="text-xs uppercase tracking-widest text-violet-400/80 font-medium">
                  Call to action
                </span>
                <h2 className="text-xl font-semibold text-zinc-50 tracking-tight pb-4">
                  {result.analysis.cta.headline}
                </h2>
                <div className="space-y-8">
                  <Section
                    label="02"
                    title="Action items"
                    items={result.analysis.cta.action_items}
                    accent="border-violet-500"
                    labelColor="text-violet-400"
                  />
                  <Section
                    label="03"
                    title="Decisions to make"
                    items={result.analysis.cta.decisions_to_make}
                    accent="border-sky-500/70"
                    labelColor="text-sky-400"
                  />
                  <Section
                    label="04"
                    title="Questions to explore"
                    items={result.analysis.cta.questions_to_explore}
                    accent="border-amber-500/70"
                    labelColor="text-amber-400"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}

function Section({
  label,
  title,
  items,
  accent = "border-zinc-700",
  labelColor = "text-zinc-500",
}: {
  label: string
  title: string
  items: string[]
  accent?: string
  labelColor?: string
}) {
  return (
    <div className={`border-l-2 ${accent} pl-4`}>
      <div className="flex items-baseline gap-3 mb-3">
        <span className={`text-xs ${labelColor} font-mono`}>{label}</span>
        <h3 className="font-semibold text-zinc-100 tracking-tight">{title}</h3>
      </div>
      <ul className="space-y-2 text-zinc-400 text-[15px] leading-relaxed">
        {items.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ul>
    </div>
  )
}

export default App