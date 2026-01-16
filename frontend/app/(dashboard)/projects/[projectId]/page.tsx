import { Button } from "@/components/ui/button"
import { ArrowRight, FileText, Bot, Settings } from "lucide-react"
import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

export default function ProjectPage({ params }: { params: { projectId: string } }) {
  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight glow-text">Legal Contract Analysis</h2>
          <p className="text-muted-foreground mt-2">
            Project configuration and quick actions.
          </p>
        </div>
        <Button variant="outline">
          <Settings className="mr-2 h-4 w-4" /> Project Settings
        </Button>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card className="glass-card hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader>
            <div className="mb-2 rounded-md bg-primary/10 w-fit p-3 group-hover:bg-primary/20 transition-colors">
              <FileText className="h-6 w-6 text-primary" />
            </div>
            <CardTitle>Knowledge Base</CardTitle>
            <CardDescription>
              Manage documents and embeddings.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="text-2xl font-bold">145</div>
              <p className="text-xs text-muted-foreground">Documents indexed</p>
            </div>
            <Button className="w-full" asChild>
              <Link href={`./${params.projectId}/documents`}> 
                {/* Note: In Next.js App Router dynamic routes, basic relative links can be tricky, but standard link works. I'll use relative for now or build path. */}
                Manage Documents <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>

        <Card className="glass-card hover:border-primary/50 transition-colors cursor-pointer group">
          <CardHeader>
            <div className="mb-2 rounded-md bg-purple-500/10 w-fit p-3 group-hover:bg-purple-500/20 transition-colors">
              <Bot className="h-6 w-6 text-purple-500" />
            </div>
            <CardTitle>Agents</CardTitle>
            <CardDescription>
              Configure retrieval agents.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="mb-4">
              <div className="text-2xl font-bold">3</div>
              <p className="text-xs text-muted-foreground">Active agents</p>
            </div>
            <Button className="w-full" variant="secondary" asChild>
              <Link href={`./${params.projectId}/agents`}>
                Manage Agents <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
