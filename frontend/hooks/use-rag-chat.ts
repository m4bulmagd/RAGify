"use client"

import { useState, useCallback } from "react"
import { apiFetch } from "@/lib/api"
import { parseSSEStream, StreamEvent } from "@/lib/stream-parser"
import { toast } from "sonner"

export interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  citations?: Citation[]
  usage?: Usage
  isStreaming?: boolean
}

export interface Citation {
  chunk_id: number
  document_id: string
  document_name: string
  content: string
  similarity_score: number
  page_number?: number
}

export interface Usage {
  model_name?: string
  latency_ms?: number
  tokens?: number
}

export function useRAGChat(agentId: string, projectId: string, sessionId?: string) {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | undefined>(sessionId)

  const sendMessage = useCallback(async (content: string) => {
    if (!content.trim() || !agentId) return

    // 1. Optimistic User Message
    const userMsgId = Date.now().toString()
    const userMsg: Message = { id: userMsgId, role: "user", content }
    
    // 2. Placeholder Assistant Message
    const assistantMsgId = (Date.now() + 1).toString()
    const assistantMsg: Message = { 
        id: assistantMsgId, 
        role: "assistant", 
        content: "", 
        isStreaming: true 
    }

    setMessages(prev => [...prev, userMsg, assistantMsg])
    setIsLoading(true)

    try {
      // 3. Initiate Request
      // If no session ID yet, we might need to create one first or let backend handle it?
      // The current backend `send_message` requires a session_id if provided, 
      // but if we are starting fresh, we might need to create it.
      // Let's assume the caller ensures a session exists OR we handle it here.
      // Actually backend `send_message` logic: "1. Get or Create Session" ... wait 
      // backend code: `if chat_request.session_id: ... else: raise HTTPException`.
      // So we MUST have a session ID.
      
      let activeSessionId = currentSessionId
      if (!activeSessionId) {
          // Auto-create session if missing
          const sessionRes = await apiFetch("/chats/sessions", {
              method: "POST",
              body: JSON.stringify({ project_id: projectId, agent_id: agentId })
          })
          if (!sessionRes.ok) throw new Error("Failed to start session")
          const sessionData = await sessionRes.json()
          activeSessionId = sessionData.id
          setCurrentSessionId(activeSessionId)
      }

      const res = await apiFetch("/chats/messages", {
        method: "POST",
        body: JSON.stringify({
          session_id: activeSessionId,
          agent_id: agentId,
          message: content,
          stream: true
        })
      })

      if (!res.ok) throw new Error("Failed to send message")

      // 4. Consume Stream
      for await (const event of parseSSEStream(res)) {
        setMessages(prev => {
          const newMessages = [...prev]
          const msgIndex = newMessages.findIndex(m => m.id === assistantMsgId)
          if (msgIndex === -1) return prev

          const msg = { ...newMessages[msgIndex] }

          switch (event.type) {
            case "content":
              msg.content += event.data
              break
            case "citation":
              msg.citations = event.data
              break
            case "usage":
              msg.usage = event.data
              break
            case "done":
              msg.isStreaming = false
              // Update real ID from backend if provided
              if (event.data?.message_id) {
                  msg.id = event.data.message_id
              }
              break
            case "error":
              toast.error(event.data)
              msg.content += "\n[Error generating response]"
              msg.isStreaming = false
              break
          }
          
          newMessages[msgIndex] = msg
          return newMessages
        })
      }

    } catch (error: any) {
      console.error("Chat error:", error)
      toast.error("Failed to send message")
      setMessages(prev => prev.map(m => 
          m.id === assistantMsgId 
            ? { ...m, isStreaming: false, content: m.content + "\n[Failed]" } 
            : m
      ))
    } finally {
      setIsLoading(false)
    }
  }, [agentId, projectId, currentSessionId])

  return {
    messages,
    sendMessage,
    isLoading,
    currentSessionId,
    setMessages // Allow setting initial history
  }
}
