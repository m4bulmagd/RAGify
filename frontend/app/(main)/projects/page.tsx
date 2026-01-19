import { CreateProjectDialog } from "@/components/projects/create-project-dialog"
import { RecentProjects } from "@/components/projects/recent-projects"

export default function ProjectsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Projects</h2>
          <p className="text-muted-foreground mt-2">
            Manage your RAG workspaces.
          </p>
        </div>
        <CreateProjectDialog />
      </div>
      
      {/* Reusing RecentProjects component but in full width/list mode conceptually */}
      <RecentProjects />
    </div>
  )
}
