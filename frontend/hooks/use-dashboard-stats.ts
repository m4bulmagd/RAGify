import { useQuery } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"

export type DashboardStats = {
  total_projects: number
  total_requests: number
  storage_usage: number
  processing_docs: number
}

export function useDashboardStats() {
  return useQuery<DashboardStats>({
    queryKey: ["dashboard-stats"],
    queryFn: async () => {
      const res = await apiFetch("/users/me/stats")
      if (!res.ok) {
        throw new Error("Failed to fetch dashboard stats")
      }
      return res.json()
    },
  })
}
