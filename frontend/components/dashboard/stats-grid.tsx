"use client"

import { 
  BarChart3, 
  Database, 
  HardDrive, 
  Zap 
} from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { useDashboardStats } from "@/hooks/use-dashboard-stats"
import { Skeleton } from "@/components/ui/skeleton"

export function StatsGrid() {
  const { data: stats, isLoading } = useDashboardStats()

  if (isLoading) {
      return (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
             {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-32 rounded-xl" />
             ))}
        </div>
    )
  }

  // Helper to format bytes
  const formatBytes = (bytes: number = 0) => {
      if (bytes === 0) return "0 B"
      const k = 1024
      const sizes = ["B", "KB", "MB", "GB", "TB"]
      const i = Math.floor(Math.log(bytes) / Math.log(k))
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i]
  }

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      <Card className="hover:bg-card/50 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Projects</CardTitle>
          <BarChart3 className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.total_projects || 0}</div>
          <p className="text-xs text-muted-foreground">
            Current active projects
          </p>
        </CardContent>
      </Card>
      
      <Card className="hover:bg-card/50 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Total Messages</CardTitle>
          <Zap className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.total_requests || 0}</div>
          <p className="text-xs text-muted-foreground">
            Messages exchanged
          </p>
        </CardContent>
      </Card>
      
      <Card className="hover:bg-card/50 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Documents Storage</CardTitle>
          <Database className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{formatBytes(stats?.storage_usage)}</div>
          <p className="text-xs text-muted-foreground">
            Total document size
          </p>
        </CardContent>
      </Card>
      
      <Card className="hover:bg-card/50 transition-colors">
        <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
          <CardTitle className="text-sm font-medium">Processing</CardTitle>
          <HardDrive className="h-4 w-4 text-primary" />
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats?.processing_docs || 0}</div>
          <p className="text-xs text-muted-foreground">
            Docs currently indexing
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
