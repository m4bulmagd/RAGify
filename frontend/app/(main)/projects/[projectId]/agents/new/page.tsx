import { AgentBuilderWizard } from "@/components/agents/agent-builder-wizard"

interface NewAgentPageProps {
  params: Promise<{
    projectId: string
  }>
}

export default async function NewAgentPage({ params }: NewAgentPageProps) {
  const { projectId } = await params

  return (
    <div className="space-y-8 animate-in fade-in duration-500 max-w-5xl mx-auto">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Create Agent</h2>
        <p className="text-muted-foreground mt-2">
          Design your RAG agent's personality and knowledge base.
        </p>
      </div>

      <AgentBuilderWizard projectId={projectId} />
    </div>
  )
}
