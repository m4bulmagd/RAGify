import { ChatInterface } from "@/components/chat/chat-interface"
import { DebugPanel } from "@/components/playground/debug-panel"

export default function PlaygroundPage() {
  return (
    <div className="flex h-[calc(100vh-6rem)] overflow-hidden rounded-xl border border-border bg-background shadow-2xl">
      <div className="flex-1 min-w-0">
         <ChatInterface />
      </div>
      <div className="w-[350px] hidden lg:block">
         <DebugPanel />
      </div>
    </div>
  )
}
