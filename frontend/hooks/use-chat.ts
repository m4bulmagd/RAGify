import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"

export interface Message {
  id: string
  session_id: string
  role: "user" | "assistant" | "system"
  content: string
  created_at: string
  sources_count: number
}

export interface ChatSession {
  id: string
  user_id: string
  project_id: string
  agent_id: string
  title: string
  status: string
  message_count: number
  last_message_at: string
  created_at: string
  messages?: Message[]
}

export interface CreateSessionData {
    project_id: string
    agent_id: string
    title?: string
}

export function useChat(projectId?: string) {
  const queryClient = useQueryClient()

  const { data: sessions, isLoading: isLoadingSessions } = useQuery<ChatSession[]>({
    queryKey: ["chat-sessions", projectId],
    queryFn: async () => {
      const res = await apiFetch(`/chats/sessions?project_id=${projectId}`)
      if (!res.ok) throw new Error("Failed to fetch sessions")
      return res.json()
    },
    enabled: !!projectId
  })

  const useSession = (sessionId: string) => useQuery<ChatSession>({
    queryKey: ["chat-session", sessionId],
    queryFn: async () => {
        const res = await apiFetch(`/chats/sessions/${sessionId}`)
        if (!res.ok) throw new Error("Failed to fetch session")
        return res.json()
    },
    enabled: !!sessionId
  })

  const createSession = useMutation({
    mutationFn: async (data: CreateSessionData) => {
        const res = await apiFetch("/chats/sessions", {
            method: "POST",
            body: JSON.stringify(data)
        })
        if (!res.ok) throw new Error("Failed to create session")
        return res.json()
    },
    onSuccess: () => {
        queryClient.invalidateQueries({ queryKey: ["chat-sessions"] })
    }
  })

  const sendMessage = useMutation({
      mutationFn: async ({ sessionId, message, agentId }: { sessionId: string, message: string, agentId: string }) => {
          const res = await apiFetch("/chats/messages", {
              method: "POST",
              body: JSON.stringify({
                  session_id: sessionId,
                  agent_id: agentId,
                  message: message,
                  stream: false // TODO: Implement streaming
              })
          })
          if (!res.ok) throw new Error("Failed to send message")
          return res.json()
      },
      onSuccess: (_, variables) => {
          queryClient.invalidateQueries({ queryKey: ["chat-session", variables.sessionId] })
          queryClient.invalidateQueries({ queryKey: ["chat-sessions"] }) 
      }
  })

  return {
    sessions,
    isLoadingSessions,
    useSession,
    createSession,
    sendMessage
  }
}
