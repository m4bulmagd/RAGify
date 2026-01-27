"use client"

import { ChatInterface } from "@/components/chat/chat-interface"
import { DebugPanel } from "@/components/playground/debug-panel"
import { useRAGChat } from "@/hooks/use-rag-chat"
import { useParams } from "next/navigation"

export default function PlaygroundPage() {
  const params = useParams()
  const agentId = params.agentId as string
  const projectId = params.projectId as string

  const { messages, sendMessage, isLoading, setMessages } = useRAGChat(agentId, projectId)
  const lastMessage = messages[messages.length - 1]

  return (
    <div className="flex h-[calc(100vh-6rem)] overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
      <div className="flex-1 min-w-0">
         <ChatInterface 
            messages={messages} 
            sendMessage={sendMessage} 
            isLoading={isLoading} 
            setMessages={setMessages}
         />
      </div>
      <div className="w-[350px] hidden lg:block">
         <DebugPanel lastMessage={lastMessage} />
      </div>
    </div>
  )
}
