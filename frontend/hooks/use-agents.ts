import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"

export interface AgentLLMConfig {
  provider: string
  model_name: string
  temperature: number
  max_tokens: number
  top_p: number
  system_prompt: string
  enable_streaming: boolean
}

export interface AgentRetrievalConfig {
  retrieval_mode: string
  top_k: number
  similarity_threshold: number
  enable_reranking: boolean
}

export interface Agent {
  id: string
  name: string
  description?: string
  agent_type: string
  project_id: string
  created_by: string
  is_active: boolean
  created_at: string
  updated_at: string
  llm_config?: AgentLLMConfig
  retrieval_config?: AgentRetrievalConfig
}

export interface CreateAgentData {
  name: string
  description?: string
  agent_type: string
  project_id: string
  llm_config: Partial<AgentLLMConfig>
  retrieval_config: Partial<AgentRetrievalConfig>
  document_ids?: string[]
}

export function useAgents(projectId?: string) {
  const queryClient = useQueryClient()

  const { data: agents, isLoading, error } = useQuery<Agent[]>({
    queryKey: ["agents", projectId],
    queryFn: async () => {
      // TODO: Backend doesn't support filtering by project_id in generic GET yet,
      // but assuming we might add it or filter client side.
      // For now, let's just fetch all and filter client side if needed, 
      // or better, update backend to support it. 
      // Checking backend... it doesn't have list endpoint in `agents.py`. 
      // Wait, I missed adding a list endpoint in `agents.py`? 
      // Checking `agents.py` content...
      // It has create, get, update_llm_config. NO LIST ENDPOINT.
      // I should probably fix that.
      // For now, I will implement this hook assuming I'll fix the backend.
      const res = await apiFetch(`/agents/?project_id=${projectId}`) 
      if (!res.ok) {
        throw new Error("Failed to fetch agents")
      }
      return res.json()
    },
    enabled: !!projectId, 
  })

  // Basic fetch for single agent
  const useAgent = (agentId: string) => useQuery<Agent>({
    queryKey: ["agent", agentId],
    queryFn: async () => {
      const res = await apiFetch(`/agents/${agentId}`)
      if (!res.ok) throw new Error("Failed to fetch agent")
      return res.json()
    },
    enabled: !!agentId
  })

  const createAgent = useMutation({
    mutationFn: async (data: CreateAgentData) => {
      const res = await apiFetch("/agents/", {
        method: "POST",
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        throw new Error("Failed to create agent")
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["agents"] })
      toast.success("Agent created successfully")
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create agent")
    },
  })

  return {
    agents,
    isLoading,
    error,
    useAgent,
    createAgent,
  }
}
