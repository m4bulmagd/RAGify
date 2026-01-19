import { StatsGrid } from "@/components/dashboard/stats-grid"
import { RecentProjects } from "@/components/projects/recent-projects"
import { ActivityFeed } from "@/components/dashboard/activity-feed"

export default function DashboardPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
          <p className="text-muted-foreground mt-2">
            Overview of your RAG agents and knowledge bases.
          </p>
        </div>
      </div>

      <StatsGrid />
      
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <RecentProjects />
        <ActivityFeed />
      </div>
    </div>
  )
}
