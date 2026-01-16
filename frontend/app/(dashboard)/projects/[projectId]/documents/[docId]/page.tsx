import { ChunkInspector } from "@/components/documents/chunk-inspector"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, FileText, CheckCircle2 } from "lucide-react"
import Link from "next/link"

export default function DocumentDetailPage({ params }: { params: { projectId: string; docId: string } }) {
  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4 animate-in fade-in duration-500">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" asChild>
          <Link href={`../`}>
            <ArrowLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div>
           <div className="flex items-center gap-3">
             <h2 className="text-2xl font-bold tracking-tight">Q3_Financials.pdf</h2>
             <Badge variant="outline" className="text-green-500 border-green-500/20 bg-green-500/10">
                <CheckCircle2 className="mr-1 h-3 w-3" /> Ready
             </Badge>
           </div>
           <p className="text-sm text-muted-foreground">
             Processed 145 chunks • 2.4 MB
           </p>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-2 gap-6 min-h-0">
        {/* Left Pane: Preview (Placeholder) */}
        <div className="border border-border rounded-lg bg-card/50 flex items-center justify-center p-8 text-muted-foreground flex-col gap-4">
          <FileText className="h-16 w-16 opacity-20" />
          <p>Document Preview Not Available</p>
          <Button variant="outline">Download PDF</Button>
        </div>

        {/* Right Pane: Chunk Inspector */}
        <div className="border border-border rounded-lg overflow-hidden h-full">
           <ChunkInspector />
        </div>
      </div>
    </div>
  )
}
