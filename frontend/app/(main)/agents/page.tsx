"use client"

import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Plus, Bot, ArrowRight, Activity } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { useAgents } from "@/hooks/use-agents"
import { formatDistanceToNow } from "date-fns"

export default function GlobalAgentsPage() {
  const { agents, isLoading } = useAgents()

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">All Agents</h2>
          <p className="text-muted-foreground mt-2">
            View and manage agents across all your projects.
          </p>
        </div>
        <Button variant="outline" asChild>
          <Link href="/projects">
             View Projects <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {isLoading ? (
            // Skeleton loader could go here
            <div className="col-span-full">Loading agents...</div>
        ) : (
            agents?.map((agent) => (
            <Card key={agent.id} className="hover:border-primary/50 transition-colors group">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <div className="flex items-center gap-2">
                    <div className="p-2 rounded-full bg-primary/10 text-primary">
                        <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex flex-col">
                        <CardTitle className="text-base">{agent.name}</CardTitle>
                        <CardDescription className="text-xs truncate max-w-37.5">{agent.description || "No description"}</CardDescription>
                    </div>
                </div>
                </CardHeader>
                <CardContent className="pt-4">
                <div className="flex justify-between items-end">
                    <div className="space-y-1">
                        <div className="flex items-center gap-2">
                            <Badge variant={agent.is_active ? 'default' : 'secondary'} className="uppercase text-[10px]">
                                {agent.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                            <span className="text-xs text-muted-foreground uppercase">{agent.llm_config?.model_name || "Unknown Model"}</span>
                        </div>
                        <p className="text-xs text-muted-foreground flex items-center gap-1">
                            <Activity className="h-3 w-3" /> 
                            {agent.updated_at ? formatDistanceToNow(new Date(agent.updated_at), { addSuffix: true }) : "Unknown"}
                        </p>
                    </div>
                    <Button size="sm" className="gap-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors" asChild>
                        <Link href={`/projects/${agent.project_id}/agents/${agent.id}/playground`}>
                            Open Playground
                        </Link>
                    </Button>
                </div>
                </CardContent>
            </Card>
            ))
        )}
        {!isLoading && agents?.length === 0 && (
            <div className="col-span-full text-center p-8 border border-dashed rounded-lg">
                <p className="text-muted-foreground">No agents found.</p>
                <Button variant="link" asChild className="mt-2">
                    <Link href="/projects">Go to Projects to create one</Link>
                </Button>
            </div>
        )}
      </div>
    </div>
  )
}
