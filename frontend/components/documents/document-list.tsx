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

const documents = [
  {
    id: "doc_1",
    name: "Q3_Financials.pdf",
    size: "2.4 MB",
    chunks: 145,
    status: "ready",
    uploaded: "2 mins ago",
  },
  {
    id: "doc_2",
    name: "contract_v2.docx",
    size: "1.1 MB",
    chunks: 0,
    status: "processing",
    uploaded: "5 mins ago",
  },
  {
    id: "doc_3",
    name: "employee_handbook.pdf",
    size: "4.8 MB",
    chunks: 890,
    status: "ready",
    uploaded: "1 hour ago",
  },
]

export function DocumentList() {
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
            {documents.map((doc) => (
              <TableRow key={doc.id} className="group cursor-pointer hover:bg-muted/50">
                <TableCell className="font-medium">
                  <div className="flex items-center gap-3">
                    <div className="rounded bg-primary/10 p-2 text-primary">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <Link href={`./documents/${doc.id}`} className="hover:underline">
                        {doc.name}
                      </Link>
                      <p className="text-xs text-muted-foreground">{doc.uploaded}</p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  {doc.status === "ready" ? (
                    <Badge variant="default" className="bg-green-500/10 text-green-500 hover:bg-green-500/20 border-green-500/20">
                      <CheckCircle2 className="mr-1 h-3 w-3" /> Ready
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="animate-pulse">
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" /> Processing
                    </Badge>
                  )}
                </TableCell>
                <TableCell>{doc.chunks > 0 ? doc.chunks : "-"}</TableCell>
                <TableCell className="text-muted-foreground">{doc.size}</TableCell>
                <TableCell className="text-right">
                  <Button variant="ghost" size="icon" className="opacity-0 group-hover:opacity-100 transition-opacity">
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
