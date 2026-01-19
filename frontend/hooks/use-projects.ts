import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"

export interface Project {
  id: string
  name: string
  description?: string
  owner_id: string
}

export type CreateProjectData = {
  name: string
  description?: string
}

export function useProjects() {
  const queryClient = useQueryClient()

  const { data: projects, isLoading, error } = useQuery<Project[]>({
    queryKey: ["projects"],
    queryFn: async () => {
      const res = await apiFetch("/projects/")
      if (!res.ok) {
        throw new Error("Failed to fetch projects")
      }
      return res.json()
    },
  })

  const createProject = useMutation({
    mutationFn: async (data: CreateProjectData) => {
      const res = await apiFetch("/projects/", {
        method: "POST",
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        throw new Error("Failed to create project")
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      toast.success("Project created successfully")
    },
    onError: (error) => {
      toast.error(error.message || "Failed to create project")
    },
  })

    const updateProject = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: CreateProjectData }) => {
      const res = await apiFetch(`/projects/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      })
      if (!res.ok) {
        throw new Error("Failed to update project")
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      toast.success("Project updated successfully")
    },
    onError: (error) => {
      toast.error(error.message || "Failed to update project")
    },
  })

  const deleteProject = useMutation({
    mutationFn: async (projectId: string) => {
      const res = await apiFetch(`/projects/${projectId}`, {
        method: "DELETE",
      })
      if (!res.ok) {
        throw new Error("Failed to delete project")
      }
      return res.json()
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["projects"] })
      toast.success("Project deleted successfully")
    },
    onError: (error) => {
      toast.error(error.message || "Failed to delete project")
    },
  })

  return {
    projects,
    isLoading,
    error,
    createProject,
    updateProject,
    deleteProject,
  }
}
