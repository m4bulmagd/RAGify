import { Button } from "@/components/ui/button"
import { Plus, Bot, MoreHorizontal, Play } from "lucide-react"
import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem } from "@/components/ui/dropdown-menu"

const agents = [
  {
    id: "agent_1",
    name: "Legal Contract Helper",
    model: "gpt-4",
    status: "active",
    deployments: 124,
  },
  {
    id: "agent_2",
    name: "Clause Extractor",
    model: "claude-3-opus",
    status: "draft",
    deployments: 0,
  },
  {
    id: "agent_3",
    name: "Risk Auditor",
    model: "gpt-3.5-turbo",
    status: "active",
    deployments: 890,
  }
]

export default function AgentsPage() {
  return (
      <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight glow-text">Agents</h2>
          <p className="text-muted-foreground mt-2">
            Configure and deploy your RAG assistants.
          </p>
        </div>
        <Button asChild>
          <Link href="./agents/new">
             <Plus className="mr-2 h-4 w-4" /> Create Agent
          </Link>
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {agents.map(agent => (
              <Card key={agent.id} className="glass-card hover:border-primary/50 transition-colors group">
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
                                  <Badge variant={agent.status === 'active' ? 'default' : 'secondary'} className="uppercase text-[10px]">
                                      {agent.status}
                                  </Badge>
                                  <span className="text-xs text-muted-foreground uppercase">{agent.model}</span>
                              </div>
                              <p className="text-xs text-muted-foreground">
                                  {agent.deployments} conversations
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
