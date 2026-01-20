"use client"

import { Button } from "@/components/ui/button"
import { Play } from "lucide-react"
import { useChat } from "@/hooks/use-chat"
import { useRouter } from "next/navigation"
import { toast } from "sonner"

interface StartChatButtonProps {
    agentId: string
    projectId: string
    agentName: string
}

export function StartChatButton({ agentId, projectId, agentName }: StartChatButtonProps) {
    const { createSession } = useChat(projectId)
    const router = useRouter()

    const handleStartChat = async () => {
        try {
            const session = await createSession.mutateAsync({
                project_id: projectId,
                agent_id: agentId,
                title: `Chat with ${agentName}`
            })
            router.push(`/chat?project_id=${projectId}&session_id=${session.id}`)
        } catch (error) {
            console.error("Failed to start chat", error)
            toast.error("Failed to start chat session")
        }
    }

    return (
        <Button 
            size="sm" 
            variant="outline" 
            className="gap-2 hover:bg-primary hover:text-primary-foreground transition-colors" 
            onClick={handleStartChat}
            disabled={createSession.isPending}
        >
            <Play className="h-3 w-3" /> 
            {createSession.isPending ? "Starting..." : "Playground"}
        </Button>
    )
}
