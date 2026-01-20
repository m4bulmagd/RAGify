"use client"

import * as React from "react"
import { UploadCloud, File, X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"
import { Button } from "@/components/ui/button"


import { useUploadDocument } from "@/hooks/use-documents"
import { useParams } from "next/navigation"

export function DocumentUploader({ projectId }: { projectId?: string }) {
  const [isDragging, setIsDragging] = React.useState(false)
  const [files, setFiles] = React.useState<File[]>([])
  
  const params = useParams()
  const pid = projectId || (params.projectId as string)
  
  const uploadDocument = useUploadDocument()
  const uploading = uploadDocument.isPending
  const [progress, setProgress] = React.useState(0) // Mock progress for now, or XHR logic if deeply integrated.

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const onDragLeave = () => {
    setIsDragging(false)
  }

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const newFiles = Array.from(e.dataTransfer.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const newFiles = Array.from(e.target.files)
      setFiles((prev) => [...prev, ...newFiles])
    }
  }

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const startUpload = async () => {
    if (!pid) return
    
    // Upload files sequentially or parallel
    await Promise.all(files.map(async (file) => {
         await uploadDocument.mutateAsync({ projectId: pid, file })
    }))
    
    setFiles([])
    setProgress(0)
  }

  return (
    <div className="w-full space-y-4">
      <div
        className={cn(
          "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-all",
          isDragging
            ? "border-primary bg-primary/10"
            : "border-muted-foreground/25 hover:border-primary/50 hover:bg-muted/50"
        )}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
      >
        <div className="flex flex-col items-center justify-center space-y-4 text-center">
          <div className="rounded-full bg-background p-4 shadow-sm ring-1 ring-border">
            <UploadCloud className="h-8 w-8 text-primary" />
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium">
              Drag & drop files or{" "}
              <label
                htmlFor="file-upload"
                className="cursor-pointer text-primary hover:underline"
              >
                browse
              </label>
            </p>
            <p className="text-xs text-muted-foreground">
              PDF, TXT, DOCX up to 10MB
            </p>
          </div>
          <input
            id="file-upload"
            type="file"
            className="hidden"
            multiple
            onChange={handleFileInput}
          />
        </div>
      </div>

      {files.length > 0 && (
        <div className="space-y-4">
          <div className="space-y-2">
            {files.map((file, i) => (
              <div
                key={i}
                className="flex items-center justify-between rounded-md border border-border bg-card/50 p-3"
              >
                <div className="flex items-center gap-3">
                  <div className="rounded bg-primary/20 p-2">
                    <File className="h-4 w-4 text-primary" />
                  </div>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{file.name}</span>
                    <span className="text-xs text-muted-foreground">
                      {(file.size / 1024 / 1024).toFixed(2)} MB
                    </span>
                  </div>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 text-destructive hover:text-destructive"
                  onClick={() => removeFile(i)}
                  disabled={uploading}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>

          {uploading && <Progress value={progress} className="h-2" />}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={() => setFiles([])} disabled={uploading}>
              Cancel
            </Button>
            <Button onClick={startUpload} disabled={uploading}>
              {uploading ? "Uploading..." : "Upload Files"}
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
