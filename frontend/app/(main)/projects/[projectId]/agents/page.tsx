"use client"

import { Button } from "@/components/ui/button"
import { Plus, Bot, MoreHorizontal, Play, Loader2 } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { useAgents } from "@/hooks/use-agents"
import { useParams } from "next/navigation"

export default function AgentsPage() {
  const params = useParams()
  const projectId = params.projectId as string
  const { agents, isLoading, error } = useAgents(projectId)

  if (isLoading) {
      return (
          <div className="flex items-center justify-center p-12">
              <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
      )
  }

  if (error) {
      return (
          <div className="p-8 text-center text-destructive">
              Failed to load agents. Please try again.
          </div>
      )
  }

  return (
      <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Agents</h2>
          <p className="text-muted-foreground mt-2">
            Configure and deploy your RAG assistants.
          </p>
        </div>
        <Button asChild>
          <Link href={`/projects/${projectId}/agents/new`}>
             <Plus className="mr-2 h-4 w-4" /> Create Agent
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {(!agents || agents.length === 0) && (
              <div className="col-span-full text-center py-12 border border-dashed rounded-lg bg-muted/50">
                  <Bot className="h-10 w-10 mx-auto text-muted-foreground mb-4" />
                  <h3 className="text-lg font-medium">No agents created yet</h3>
                  <p className="text-muted-foreground mb-6">Create your first AI agent to get started.</p>
                  <Button asChild>
                    <Link href={`/projects/${projectId}/agents/new`}>
                        Create Agent
                    </Link>
                  </Button>
              </div>
          )}
          {agents?.map(agent => (
              <Card key={agent.id} className="hover:border-primary/50 transition-colors group">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <div className="flex items-center gap-2">
                          <div className="p-2 rounded-full bg-primary/10 text-primary">
                              <Bot className="h-4 w-4" />
                          </div>
                          <CardTitle className="text-base truncate max-w-[150px]" title={agent.name}>{agent.name}</CardTitle>
                      </div>
                      <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                              <Button variant="ghost" size="icon" className="h-8 w-8">
                                  <MoreHorizontal className="h-4 w-4" />
                              </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                              <DropdownMenuItem>Edit Configuration</DropdownMenuItem>
                              <DropdownMenuItem>View Analytics</DropdownMenuItem>
                              <DropdownMenuItem className="text-destructive">Delete</DropdownMenuItem>
                          </DropdownMenuContent>
                      </DropdownMenu>
                  </CardHeader>
                  <CardContent className="pt-4">
                      <div className="flex justify-between items-end">
                          <div className="space-y-1">
                              <div className="flex items-center gap-2">
                                  <Badge variant={agent.is_active ? 'default' : 'secondary'} className="uppercase text-[10px]">
                                      {agent.is_active ? 'Active' : 'Inactive'}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground uppercase truncate max-w-[100px]">
                                      {agent.llm_config?.model_name || 'N/A'}
                                  </span>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                  {/* Placeholder for stats */}
                                  0 conversations
                              </p>
                          </div>
                          <Button size="sm" variant="outline" className="gap-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors" asChild>
                              <Link href={`./agents/${agent.id}/playground`}>
                                  <Play className="h-3 w-3" /> Playground
                              </Link>
                          </Button>
                      </div>
                  </CardContent>
              </Card>
          ))}
      </div>
    </div>
  )
}
