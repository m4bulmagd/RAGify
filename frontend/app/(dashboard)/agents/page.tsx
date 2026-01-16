import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Plus, Bot, ArrowRight, Activity } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

const allAgents = [
  {
    id: "agent_1",
    name: "Legal Contract Helper",
    project: "Legal Contract Analysis",
    projectId: "proj_1",
    model: "gpt-4",
    status: "active",
    lastActive: "2 mins ago",
  },
  {
    id: "agent_3",
    name: "Risk Auditor",
    project: "Financial Reports Q3",
    projectId: "proj_3",
    model: "gpt-3.5-turbo",
    status: "active",
    lastActive: "1 hour ago",
  },
  {
    id: "agent_2",
    name: "Clause Extractor",
    project: "Legal Contract Analysis",
    projectId: "proj_1",
    model: "claude-3-opus",
    status: "draft",
    lastActive: "2 days ago",
  },
]

export default function GlobalAgentsPage() {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight glow-text">All Agents</h2>
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
        {allAgents.map((agent) => (
          <Card key={agent.id} className="glass-card hover:border-primary/50 transition-colors group">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
               <div className="flex items-center gap-2">
                  <div className="p-2 rounded-full bg-primary/10 text-primary">
                      <Bot className="h-4 w-4" />
                  </div>
                  <div className="flex flex-col">
                      <CardTitle className="text-base">{agent.name}</CardTitle>
                      <CardDescription className="text-xs">{agent.project}</CardDescription>
                  </div>
               </div>
            </CardHeader>
            <CardContent className="pt-4">
               <div className="flex justify-between items-end">
                  <div className="space-y-1">
                      <div className="flex items-center gap-2">
                          <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="uppercase text-[10px]">
                              {agent.status}
                          </Badge>
                          <span className="text-xs text-muted-foreground uppercase">{agent.model}</span>
                      </div>
                      <p className="text-xs text-muted-foreground flex items-center gap-1">
                          <Activity className="h-3 w-3" /> {agent.lastActive}
                      </p>
                  </div>
                  <Button size="sm" className="gap-2 group-hover:bg-primary group-hover:text-primary-foreground transition-colors" asChild>
                      <Link href={`./projects/${agent.projectId}/agents/${agent.id}/playground`}>
                          Open Playground
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
