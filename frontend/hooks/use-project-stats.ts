import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import { useParams } from "next/navigation"

export type ProjectStats = {
  total_documents: number
  active_agents: number
  total_chunks: number
  avg_retrieval_score: number
}

export function useProjectStats(projectId?: string) {
  const params = useParams()
  const pid = projectId || (params.projectId as string)

  return useQuery<ProjectStats>({
    queryKey: ["project-stats", pid],
    queryFn: async () => {
      const res = await apiFetch(`/projects/${pid}/stats`)
      if (!res.ok) {
        throw new Error("Failed to fetch project stats")
      }
      return res.json()
    },
    enabled: !!pid,
  })
}
