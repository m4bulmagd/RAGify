import { StatsGrid } from "@/components/dashboard/stats-grid"
import { RecentProjects } from "@/components/dashboard/recent-projects"
import { ActivityFeed } from "@/components/dashboard/activity-feed"
import { Button } from "@/components/ui/button"
import { Plus } from "lucide-react"

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight glow-text">Dashboard</h2>
          <p className="text-muted-foreground mt-2">
            Overview of your RAG agents and knowledge bases.
          </p>
        </div>
        <Button className="glass bg-primary/20 hover:bg-primary/30 text-primary-foreground border-primary/50">
          <Plus className="mr-2 h-4 w-4" /> New Project
        </Button>
      </div>

      <StatsGrid />
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <RecentProjects />
        <ActivityFeed />
      </div>
    </div>
  )
}
