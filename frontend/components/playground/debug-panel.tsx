import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Activity, Search, Database } from "lucide-react"

import { Message } from "@/hooks/use-rag-chat"

interface DebugPanelProps {
  lastMessage?: Message
}

export function DebugPanel({ lastMessage }: DebugPanelProps) {
  return (
    <div className="h-full border-l border-border bg-sidebar-background flex flex-col">
       <div className="p-4 border-b border-border flex items-center justify-between">
           <h3 className="font-heading font-semibold text-sm">System Internals</h3>
           <Badge variant="outline" className="border-primary/20 text-primary">Live</Badge>
       </div>

       <Tabs defaultValue="trace" className="flex-1 flex flex-col min-h-0">
          <div className="px-4 pt-2">
            <TabsList className="w-full">
                <TabsTrigger value="trace" className="flex-1">Trace</TabsTrigger>
                <TabsTrigger value="retrieval" className="flex-1">Retrieval</TabsTrigger>
            </TabsList>
          </div>
          
          <TabsContent value="trace" className="flex-1 overflow-hidden mt-0">
             <ScrollArea className="h-full">
                <div className="p-4 space-y-4 font-mono text-xs">
                    <TraceItem 
                        step="USER_INPUT"
                        time="0ms"
                        data={lastMessage?.role === "user" ? lastMessage.content : "Waiting for input..."}
                    />
                     <TraceItem 
                        step="LLM_CALL"
                        time={lastMessage?.usage?.latency_ms ? `${lastMessage.usage.latency_ms}ms` : "-"}
                        data={lastMessage?.usage?.model_name || "Waiting for response..."}
                        color="text-green-500"
                    />
                     <TraceItem 
                        step="GENERATION"
                        time="-"
                        data={lastMessage?.isStreaming ? "Streaming..." : "Completed"}
                        color={lastMessage?.isStreaming ? "text-orange-500" : "text-gray-500"}
                    />
                </div>
             </ScrollArea>
          </TabsContent>

          <TabsContent value="retrieval" className="flex-1 overflow-hidden mt-0">
              <ScrollArea className="h-full">
                  <div className="p-4 space-y-3">
                      {lastMessage?.citations ? (
                          lastMessage.citations.map((citation, i) => (
                              <div key={i} className="p-3 border border-border rounded bg-card/50 hover:border-primary/50 transition-colors">
                                  <div className="flex justify-between items-center mb-1">
                                      <Badge variant="secondary" className="text-[10px] h-5">Chunk #{citation.chunk_id}</Badge>
                                      <span className="font-mono text-[10px] text-primary">{citation.similarity_score.toFixed(4)}</span>
                                  </div>
                                  <p className="text-xs text-muted-foreground line-clamp-3">
                                      {citation.content}
                                  </p>
                              </div>
                          ))
                      ) : (
                          <div className="text-center text-muted-foreground text-xs py-4">
                              No citations available
                          </div>
                      )}
                  </div>
              </ScrollArea>
          </TabsContent>
       </Tabs>
    </div>
  )
}

function TraceItem({ step, time, data, color }: { step: string, time: string, data: string, color?: string }) {
    return (
        <div className="relative pl-4 border-l border-border pb-4 last:pb-0">
            <div className={`absolute left-[-2.5px] top-1.5 h-1.5 w-1.5 rounded-full ${color?.replace('text-', 'bg-') || 'bg-foreground'}`} />
            <div className="flex justify-between items-start">
               <span className={`font-bold ${color || 'text-foreground'}`}>{step}</span>
               <span className="text-muted-foreground opacity-50">{time}</span>
            </div>
            <div className="mt-1 text-muted-foreground break-all">
                {data}
            </div>
        </div>
    )
}
