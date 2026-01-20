"use client"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, Loader2, MoreVertical, Search, CheckCircle2 } from "lucide-react"
import Link from "next/link"

import { useDocuments } from "@/hooks/use-documents"
import { formatDistanceToNow } from "date-fns"
import { Skeleton } from "@/components/ui/skeleton"

export function DocumentList({ projectId }: { projectId?: string }) {
  const { documents, isLoading } = useDocuments(projectId)

  if (isLoading) {
    return (
      <div className="space-y-4">
        {[1, 2].map((i) => (
          <Skeleton key={i} className="h-16 w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="rounded-md border border-border bg-card">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[400px]">Name</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Chunks</TableHead>
              <TableHead>Size</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents?.length === 0 ? (
                <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                        No documents found. Upload one to get started.
                    </TableCell>
                </TableRow>
            ) : (
            documents?.map((doc) => (
              <TableRow key={doc.id} className="group cursor-pointer hover:bg-muted/50">
                <TableCell className="font-medium">
                  <div className="flex items-center gap-3">
                    <div className="rounded bg-primary/10 p-2 text-primary">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <Link href={`./documents/${doc.id}`} className="hover:underline">
                        {doc.filename}
                      </Link>
                      <p className="text-xs text-muted-foreground">
                          {formatDistanceToNow(new Date(doc.created_at), { addSuffix: true })}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  {doc.status === "completed" ? ( // Check backend enum
                    <Badge variant="default" className="bg-green-500/10 text-green-500 hover:bg-green-500/20 border-green-500/20">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Ready
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="animate-pulse">
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" /> {doc.status}
                    </Badge>
                  )}
                </TableCell>
                <TableCell>{doc.chunks ? doc.chunks.length : "-"}</TableCell>
                <TableCell className="text-muted-foreground">{(doc.size / 1024 / 1024).toFixed(2)} MB</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
