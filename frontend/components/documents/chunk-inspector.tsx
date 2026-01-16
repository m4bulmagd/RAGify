import { Badge } from "@/components/ui/badge"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"

interface Chunk {
  id: string
  content: string
  score?: number
  index: number
}

// Mock Data
const chunks: Chunk[] = Array.from({ length: 50 }).map((_, i) => ({
  id: `chunk_${i}`,
  index: i,
  content: `This is a sample chunk of text extracted from the document. It contains relevant information for retrieval. Section ${i + 1}. The quick brown fox jumps over the lazy dog. Vector embeddings are cool.`,
  score: Math.random(),
}))

export function ChunkInspector() {
  return (
    <div className="h-full flex flex-col border-l border-border bg-sidebar-background">
      <div className="p-4 border-b border-border">
        <h3 className="font-heading font-semibold">Chunk Inspector</h3>
        <p className="text-xs text-muted-foreground">
          {chunks.length} chunks extracted
        </p>
      </div>
      <ScrollArea className="flex-1">
        <div className="p-4 space-y-4">
          {chunks.map((chunk) => (
            <div
              key={chunk.id}
              className="group relative rounded-lg border border-border bg-card p-3 text-sm transition-all hover:border-primary/50 hover:shadow-md"
            >
              <div className="mb-2 flex items-center justify-between">
                <Badge variant="secondary" className="text-[10px] font-mono">
                  #{chunk.index}
                </Badge>
                <span className="font-mono text-[10px] text-muted-foreground">
                  Score: {chunk.score?.toFixed(4)}
                </span>
              </div>
              <p className="text-muted-foreground leading-relaxed group-hover:text-foreground transition-colors">
                {chunk.content}
              </p>
              
              <div className="absolute inset-0 rounded-lg ring-1 ring-inset ring-primary/0 transition-all group-hover:ring-primary/20" />
            </div>
          ))}
        </div>
      </ScrollArea>
    </div>
  )
}
