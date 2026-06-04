import { useRef, useState } from "react"
import type { DragEvent, ChangeEvent } from "react"
import { Button } from "@/components/button"

type FileDropZoneProps = {
  files: File[]
  onFilesChange: (files: File[]) => void
  accept?: string
}

export function FileDropZone({
  files,
  onFilesChange,
  accept = ".pdf,.txt",
}: FileDropZoneProps) {
  const [dragDepth, setDragDepth] = useState(0)
  const isDragging = dragDepth > 0
  const inputRef = useRef<HTMLInputElement>(null)

  // ───── Helpers ─────

  // Add new files to the existing list, deduped by name+size.
  // We dedupe so dragging the same file twice doesn't create duplicates.
  function addFiles(newFiles: FileList | File[]) {
    const incoming = Array.from(newFiles)
    const existingKeys = new Set(files.map((f) => `${f.name}-${f.size}`))
    const fresh = incoming.filter(
      (f) => !existingKeys.has(`${f.name}-${f.size}`),
    )
    onFilesChange([...files, ...fresh])
  }

  function removeFile(index: number) {
    onFilesChange(files.filter((_, i) => i !== index))
  }

  function clearAll() {
    onFilesChange([])
    if (inputRef.current) inputRef.current.value = ""
  }

  // ───── Drag handlers ─────

  function handleDragEnter(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragDepth((d) => d + 1)
  }
  function handleDragOver(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
  }
  function handleDragLeave(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragDepth((d) => Math.max(0, d - 1))
  }
  function handleDrop(e: DragEvent<HTMLDivElement>) {
    e.preventDefault()
    setDragDepth(0)
    if (e.dataTransfer.files.length > 0) {
      addFiles(e.dataTransfer.files)
    }
  }

  // ───── Click handlers ─────

  function handleClick() {
    inputRef.current?.click()
  }
  function handleInputChange(e: ChangeEvent<HTMLInputElement>) {
    if (e.target.files && e.target.files.length > 0) {
      addFiles(e.target.files)
    }
  }
  function handleStopPropagation(e: React.MouseEvent) {
    // Prevent clicks inside the file list from bubbling up and reopening
    // the file picker.
    e.stopPropagation()
  }

  return (
    <div className="space-y-3">
      <div
        onClick={handleClick}
        onDragEnter={handleDragEnter}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`
          relative cursor-pointer rounded-lg border-2 border-dashed
          px-6 py-8 text-center transition-colors
          ${
            isDragging
              ? "border-violet-400 bg-violet-500/10"
              : "border-zinc-800 bg-zinc-900/40 hover:border-zinc-700 hover:bg-zinc-900/60"
          }
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          multiple
          onChange={handleInputChange}
          className="hidden"
        />

        <div className="space-y-2 pointer-events-none">
          <p className="text-sm text-zinc-300">
            {isDragging
              ? "Drop them here"
              : files.length > 0
              ? "Drop or click to add more"
              : "Drop files or click to browse"}
          </p>
          <p className="text-xs text-zinc-500">
            PDF or TXT · combine multiple parts into one analysis
          </p>
        </div>
      </div>

      {files.length > 0 && (
        <div
          onClick={handleStopPropagation}
          className="rounded-lg border border-zinc-800 bg-zinc-900/40 divide-y divide-zinc-800"
        >
          {files.map((file, i) => (
            <div
              key={`${file.name}-${file.size}-${i}`}
              className="flex items-center justify-between gap-4 px-4 py-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <span className="text-xs font-mono text-zinc-600 shrink-0">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div className="min-w-0">
                  <p className="text-sm text-zinc-200 truncate">{file.name}</p>
                  <p className="text-xs text-zinc-500">
                    {(file.size / 1024).toFixed(1)} KB
                  </p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => removeFile(i)}
                className="text-xs text-zinc-500 hover:text-red-400 transition-colors shrink-0"
              >
                Remove
              </button>
            </div>
          ))}
          <div className="flex justify-between items-center px-4 py-2 bg-zinc-900/60">
            <p className="text-xs text-zinc-500">
              {files.length} file{files.length === 1 ? "" : "s"} · combined into one analysis
            </p>
            <Button
              type="button"
              size="sm"
              variant="destructive"
              onClick={clearAll}
              className="bg-red-500/15 text-red-300 border border-red-500/30 hover:bg-red-500/25 hover:text-red-200"
            >
              Clear all
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}