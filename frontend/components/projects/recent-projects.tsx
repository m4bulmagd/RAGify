"use client"

import Link from "next/link"
import { ArrowRight, MoreHorizontal, Trash2 } from "lucide-react"

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useProjects } from "@/hooks/use-projects"
import { formatDistanceToNow } from "date-fns"

import { useState } from "react"
import { EditProjectDialog } from "@/components/projects/edit-project-dialog"
import { Project } from "@/hooks/use-projects"

export function RecentProjects() {
  const { projects, isLoading, deleteProject } = useProjects()
  const [editingProject, setEditingProject] = useState<Project | null>(null)

  if (isLoading) {
    return (
      <Card className="col-span-3">
        <CardHeader>
          <CardTitle>Recent Projects</CardTitle>
          <CardDescription>Loading projects...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
             {/* Simple skeleon loading state */}
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-20 w-full animate-pulse rounded-lg bg-muted/50" />
            ))}
          </div>
        </CardContent>
      </Card>
    )
  }

  // Ensure we sort by latest or something if API doesn't? API currently just returns all.
  // Ideally backend should return sorted or we sort here. 
  // Let's assume backend might not sort yet, so simple client reverse for "recent" roughly if append-only, 
  // but better to rely on backend eventually. For now just render.
  
  const displayProjects = projects || []

  return (
    <>
      <Card className="col-span-3">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>
                You have {displayProjects.length} active workspace projects.
              </CardDescription>
            </div>
            <Button variant="outline" size="sm" asChild>
              <Link href="/projects">
                View All <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {displayProjects.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                  No projects found. Create one to get started.
              </div>
          ) : (
          <div className="space-y-4">
            {displayProjects.map((project) => (
              <div
                key={project.id}
                className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4 transition-all hover:bg-muted/50"
              >
                <div className="flex flex-col gap-1">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold">{project.name}</span>
                    <Badge variant="default" className="text-[10px] uppercase">
                      Active
                    </Badge>
                  </div>
                  <span className="text-sm text-muted-foreground line-clamp-1">
                    {project.description || "No description"}
                  </span>
                </div>
                <div className="flex items-center gap-4">
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" className="h-8 w-8">
                        <MoreHorizontal className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem>View Project</DropdownMenuItem>
                      <DropdownMenuItem onClick={() => setEditingProject(project)}>
                        Settings
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem 
                          className="text-destructive focus:text-destructive"
                          onClick={() => {
                              if (confirm("Are you sure you want to delete this project?")) {
                                  deleteProject.mutate(project.id)
                              }
                          }}
                      >
                        <Trash2 className="mr-2 h-4 w-4" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            ))}
          </div>
          )}
        </CardContent>
      </Card>
      
      {editingProject && (
        <EditProjectDialog
          project={editingProject}
          open={!!editingProject}
          onOpenChange={(open) => !open && setEditingProject(null)}
        />
      )}
    </>
  )
}
