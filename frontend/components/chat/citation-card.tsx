import { HoverCard, HoverCardContent, HoverCardTrigger } from "@/components/ui/hover-card"
import { Badge } from "@/components/ui/badge"
import { FileText } from "lucide-react"

interface CitationProps {
  id: string
  source: string
  page?: number
  score: number
  text: string
}

export function Citation({ id, source, page, score, text }: CitationProps) {
  return (
    <HoverCard>
      <HoverCardTrigger asChild>
        <Badge 
          variant="outline" 
          className="ml-1 mr-1 cursor-help gap-1 border-primary/30 bg-primary/5 text-primary hover:bg-primary/10 transition-colors"
        >
          <span className="font-mono text-[10px]">{id}</span>
        </Badge>
      </HoverCardTrigger>
      <HoverCardContent className="w-80 glass-card">
        <div className="flex justify-between space-x-4">
          <div className="space-y-1">
            <h4 className="text-sm font-semibold flex items-center gap-2">
                <FileText className="h-3 w-3" />
                {source}
            </h4>
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
                {page && <span>Page {page}</span>}
                <span>Score: {score.toFixed(3)}</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2 border-l-2 border-primary/50 pl-2 italic">
              "{text.slice(0, 100)}..."
            </p>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  )
}
