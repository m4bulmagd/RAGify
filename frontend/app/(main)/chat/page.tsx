"use client"

import { useState, useEffect, useRef } from "react"
import { useSearchParams } from "next/navigation"
import { useChat, ChatSession, Message } from "@/hooks/use-chat"
import { useAgents } from "@/hooks/use-agents"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Separator } from "@/components/ui/separator"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Send, Bot, User, MessageSquare, Plus } from "lucide-react"

export default function ChatPage() {
  const searchParams = useSearchParams()
  const projectId = searchParams.get("project_id") // Optional filter
  const sessionIdParam = searchParams.get("session_id")
  
  const { sessions, isLoadingSessions, useSession, sendMessage, createSession } = useChat(projectId || undefined)
  const { agents } = useAgents(projectId || undefined)
  
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(sessionIdParam)
  const [inputMessage, setInputMessage] = useState("")

  // Update selected session if URL changes
  useEffect(() => {
      if (sessionIdParam) {
          setSelectedSessionId(sessionIdParam)
      }
  }, [sessionIdParam])

  // Fetch details for selected session
  const { data: activeSession, isLoading: isLoadingActiveSession } = useSession(selectedSessionId || "")

  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [activeSession?.messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || !selectedSessionId || !activeSession) return

    const currentMsg = inputMessage
    setInputMessage("") // Optimistic clear

    try {
        await sendMessage.mutateAsync({
            sessionId: selectedSessionId,
            message: currentMsg,
            agentId: activeSession.agent_id // We need agent_id from session
        })
    } catch (error) {
        console.error("Failed to send", error)
        // Restore message on failure?
    }
  }
  
  const handleCreateSession = async (agentId: string) => {
      try {
          const newSession = await createSession.mutateAsync({
              project_id: projectId || "", // TODO: How to handle global chat? For now valid project required?
              agent_id: agentId, 
              title: "New Chat"
          })
          setSelectedSessionId(newSession.id)
      } catch (e) {
          console.error(e)
      }
  }

  return (
    <div className="flex h-[calc(100vh-4rem)]">
      {/* Sidebar - Sessions List */}
      <div className="w-80 border-r bg-muted/20 flex flex-col">
        <div className="p-4 border-b flex items-center justify-between">
            <h2 className="font-semibold">Chats</h2>
            <Button variant="ghost" size="icon" onClick={() => setSelectedSessionId(null)}>
                <Plus className="h-4 w-4" />
            </Button>
        </div>
        <ScrollArea className="flex-1">
            <div className="p-2 space-y-2">
                {isLoadingSessions ? (
                    <div className="p-4 text-sm text-muted-foreground">Loading chats...</div>
                ) : (
                    sessions?.map(session => (
                        <div 
                            key={session.id}
                            onClick={() => setSelectedSessionId(session.id)}
                            className={`p-3 rounded-lg text-sm cursor-pointer hover:bg-accent ${selectedSessionId === session.id ? "bg-accent" : ""}`}
                        >
                            <div className="font-medium truncate">{session.title}</div>
                            <div className="text-xs text-muted-foreground mt-1 flex justify-between">
                                <span>{session.message_count} msgs</span>
                                {/* <span>{new Date(session.updated_at).toLocaleDateString()}</span> */}
                            </div>
                        </div>
                    ))
                )}
                {sessions?.length === 0 && (
                    <div className="p-4 text-center text-sm text-muted-foreground">No active chats</div>
                )}
            </div>
        </ScrollArea>
      </div>

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {!selectedSessionId ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4">
                <MessageSquare className="h-12 w-12 text-muted-foreground" />
                <h3 className="text-lg font-medium">Select a Chat or Start a New One</h3>
                <p className="text-muted-foreground max-w-sm">
                    Choose an existing conversation from the sidebar or select an agent below to start a new chat.
                </p>
                
                {/* Agent Selection for New Chat */}
                <div className="grid grid-cols-2 gap-4 w-full max-w-2xl mt-8">
                    {agents?.map(agent => (
                        <Card key={agent.id} className="cursor-pointer hover:border-primary" onClick={() => handleCreateSession(agent.id)}>
                            <CardContent className="p-4 flex items-center gap-3">
                                <div className="p-2 bg-primary/10 rounded-full">
                                    <Bot className="h-4 w-4 text-primary" />
                                </div>
                                <div className="text-left">
                                    <div className="font-medium">{agent.name}</div>
                                    <div className="text-xs text-muted-foreground truncate">{agent.llm_config?.model_name}</div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            </div>
        ) : (
            <>
                <div className="p-4 border-b flex items-center justify-between">
                    <div>
                         <div className="font-medium">{activeSession?.title || "Chat"}</div>
                         <div className="text-xs text-muted-foreground">
                            {/* Agent Name? Backend doesn't return agent name in session yet. */}
                            Agent ID: {activeSession?.agent_id}
                         </div>
                    </div>
                </div>
                
                <ScrollArea className="flex-1 p-4">
                    <div className="space-y-4 max-w-3xl mx-auto">
                        {isLoadingActiveSession ? (
                            <div>Loading messages...</div>
                        ) : (
                           activeSession?.messages?.map(msg => (
                               <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                   {msg.role !== 'user' && (
                                       <Avatar className="h-8 w-8 mt-1">
                                           <AvatarFallback>AI</AvatarFallback>
                                       </Avatar>
                                   )}
                                   <div className={`rounded-lg p-3 max-w-[80%] ${
                                       msg.role === 'user' 
                                       ? 'bg-primary text-primary-foreground' 
                                       : 'bg-muted'
                                   }`}>
                                       {msg.content}
                                   </div>
                                    {msg.role === 'user' && (
                                       <Avatar className="h-8 w-8 mt-1">
                                           <AvatarFallback>ME</AvatarFallback>
                                       </Avatar>
                                   )}
                               </div>
                           ))
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </ScrollArea>

                <div className="p-4 border-t">
                    <div className="max-w-3xl mx-auto flex gap-2">
                        <Input 
                            value={inputMessage}
                            onChange={(e) => setInputMessage(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSendMessage()}
                            placeholder="Type a message..."
                            className="flex-1"
                        />
                        <Button onClick={handleSendMessage} disabled={!inputMessage.trim() || sendMessage.isPending}>
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </>
        )}
      </div>
    </div>
  )
}
