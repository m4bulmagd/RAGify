import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { apiFetch } from "@/lib/api"
import { toast } from "sonner"
import { useParams } from "next/navigation"

export type Document = {
  id: string
  filename: string
  file_type: string
  size: number
  status: "pending" | "processing" | "completed" | "failed"
  created_at: string
  url: string
  chunk_count: number
}

export function useDocuments(projectId?: string) {
  // If not provided, try to get from params, but usually passed explicitly
  const params = useParams()
  const pid = projectId || (params.projectId as string)

  const { data, isLoading, error } = useQuery<Document[]>({
    queryKey: ["documents", pid],
    queryFn: async () => {
        if(!pid) return []
        const res = await apiFetch(`/documents/?project_id=${pid}`)
        return res.json()
    },
    enabled: !!pid
  })
  
  return { documents: data, isLoading, error }
}

export function useUploadDocument() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ projectId, file }: { projectId: string; file: File }) => {
      const formData = new FormData()
      formData.append("file", file)
      
      const res = await apiFetch(`/documents/?project_id=${projectId}`, {
        method: "POST",
        body: formData,
      })
      
      if (!res.ok) {
          const errorData = await res.json().catch(() => ({}))
          throw new Error(errorData.detail || "Upload failed")
      }
      return res.json()
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ["documents", variables.projectId] })
      toast.success(`Uploaded ${variables.file.name} successfully`)
    },
    onError: (error, variables) => {
      toast.error(`Failed to upload ${variables.file.name}: ${error.message}`)
      console.error(error)
    },
  })
}
