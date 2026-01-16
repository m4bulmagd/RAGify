import { RecentProjects } from "@/components/dashboard/recent-projects"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function ProjectsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight glow-text">Projects</h2>
          <p className="text-muted-foreground mt-2">
            Manage your RAG workspaces.
          </p>
        </div>
        <Button>
          <Plus className="mr-2 h-4 w-4" /> New Project
        </Button>
      </div>
      
      {/* Reusing RecentProjects component but in full width/list mode conceptually */}
      <RecentProjects />
    </div>
  )
}
