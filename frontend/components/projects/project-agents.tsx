"use client"

import { Button } from "@/components/ui/button"
import { Plus, Bot, MoreHorizontal, Play, Activity } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"
import { useAgents } from "@/hooks/use-agents"
import { formatDistanceToNow } from "date-fns"
import { StartChatButton } from "@/components/chat/start-chat-button"

export function ProjectAgents({ projectId }: { projectId: string }) {
  const { agents, isLoading } = useAgents(projectId)

  return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
            <div>
                <h3 className="text-lg font-medium">Agents</h3>
                <p className="text-sm text-muted-foreground">Configure and deploy your RAG assistants.</p>
            </div>
            <Button asChild>
                <Link href={`./${projectId}/agents/new`}> {/* Or open modal */}
                    <Plus className="mr-2 h-4 w-4" /> Create Agent
                </Link>
            </Button>
        </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {isLoading ? (
               <div className="col-span-full">Loading agents...</div>
          ) : (
             agents?.map(agent => (
              <Card key={agent.id} className="hover:border-primary/50 transition-colors group">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                      <div className="flex items-center gap-2">
                          <div className="p-2 rounded-full bg-primary/10 text-primary">
                              <Bot className="h-4 w-4" />
                          </div>
                          <CardTitle className="text-base">{agent.name}</CardTitle>
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
                                  <span className="text-xs text-muted-foreground uppercase">{agent.llm_config?.model_name || "Unknown"}</span>
                              </div>
                               <p className="text-xs text-muted-foreground flex items-center gap-1">
                                    <Activity className="h-3 w-3" /> 
                                    {agent.updated_at ? formatDistanceToNow(new Date(agent.updated_at), { addSuffix: true }) : "Unknown"}
                                </p>
                          </div>
                          <Button size="sm" variant="outline" className="gap-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors" asChild>
                              <StartChatButton 
                                agentId={agent.id} 
                                projectId={projectId}
                                agentName={agent.name} 
                              />
                          </Button>
                      </div>
                  </CardContent>
              </Card>
             ))
          )}
          {!isLoading && agents?.length === 0 && (
             <div className="col-span-full text-center p-8 border border-dashed rounded-lg">
                <p className="text-muted-foreground">No agents found for this project.</p>
             </div>
          )}
      </div>
    </div>
  )
}
