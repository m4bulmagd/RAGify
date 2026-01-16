"use client"

import { useChat } from "@ai-sdk/react"
import { Send, User as UserIcon, Bot, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Citation } from "@/components/chat/citation-card"
import * as React from "react"
import { cn } from "@/lib/utils"

export function ChatInterface() {
// @ts-ignore
  const { messages, sendMessage, append, status, reload } = useChat({
      initialMessages: [
          {
              id: 'welcome',
              role: 'assistant',
              content: 'Hello! I am ready to help you analyze your documents. What would you like to know?',
          }
      ]
  } as any) as any
  
  // Normalize send method
  const send = sendMessage || append
  
  const [input, setInput] = React.useState("")
  const isLoading = status === "streaming" || status === "submitted"

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    send({ role: 'user', content: input })
    setInput("")
  }
  
  const scrollRef = React.useRef<HTMLDivElement>(null)

  React.useEffect(() => {
    if (scrollRef.current) {
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  return (
    <div className="flex flex-col h-full bg-background relative">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-6" ref={scrollRef}>
        {messages.map((m: any) => (
          <div
            key={m.id}
            className={cn(
              "flex w-full max-w-3xl mx-auto gap-4",
              m.role === "user" ? "flex-row-reverse" : "flex-row"
            )}
          >
            {/* Avatar */}
            <div className={cn(
                "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center border",
                m.role === "user" 
                  ? "bg-primary text-primary-foreground border-primary" 
                  : "bg-muted text-muted-foreground border-border"
            )}>
                {m.role === "user" ? <UserIcon className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
            </div>

            {/* Bubble */}
            <div className={cn(
                "relative group flex flex-col gap-2 min-w-[120px]",
                m.role === "user" ? "items-end" : "items-start"
            )}>
                 <div className={cn(
                    "rounded-2xl px-4 py-3 text-sm shadow-sm",
                    m.role === "user"
                      ? "bg-primary text-primary-foreground rounded-br-sm"
                      : "bg-card border border-border rounded-bl-sm"
                 )}>
                    {m.content}
                    
                    {/* Mock Citations for Assistant */}
                    {m.role === "assistant" && m.id !== 'welcome' && (
                       <div className="mt-3 flex flex-wrap gap-2 pt-2 border-t border-border/50">
                           <Citation id="1" source="contract_v2.docx" page={4} score={0.88} text="This content matches..." />
                           <Citation id="2" source="handbook.pdf" page={12} score={0.77} text="Another distinct match..." />
                       </div>
                    )}
                 </div>
            </div>
          </div>
        ))}
        {isLoading && (
            <div className="flex w-full max-w-3xl mx-auto gap-4">
                 <div className="flex-shrink-0 w-8 h-8 rounded-full bg-muted border border-border flex items-center justify-center">
                    <Bot className="w-4 h-4 animate-pulse" />
                 </div>
                 <div className="flex items-center gap-1 h-10">
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.3s]" />
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce [animation-delay:-0.15s]" />
                    <div className="w-2 h-2 bg-primary/40 rounded-full animate-bounce" />
                 </div>
            </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 pb-6 border-t border-border bg-background/50 backdrop-blur-md">
         <form onSubmit={handleSubmit} className="max-w-3xl mx-auto relative flex items-center gap-2">
            <Button 
                type="button" 
                variant="ghost" 
                size="icon" 
                onClick={() => reload()}
                className="text-muted-foreground hover:text-foreground"
            >
                <RefreshCw className="h-4 w-4" />
            </Button>
            <div className="relative flex-1">
                <Input 
                    value={input}
                    onChange={handleInputChange}
                    placeholder="Ask a question about your documents..." 
                    className="pr-12 bg-muted/50 border-transparent focus:bg-background focus:border-ring transition-all shadow-inner h-12"
                />
                <Button 
                    type="submit" 
                    size="icon"
                    className="absolute right-1 top-1 h-10 w-10 bg-primary text-primary-foreground hover:bg-primary/90 shadow-md transition-all active:scale-95"
                    disabled={isLoading || !input.trim()}
                >
                    <Send className="h-4 w-4" />
                </Button>
            </div>
         </form>
         <div className="text-center mt-2">
            <p className="text-[10px] text-muted-foreground">
                AI can make mistakes. Please review generated information.
            </p>
         </div>
      </div>
    </div>
  )
}
