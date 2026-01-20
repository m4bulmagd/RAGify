"use client"

import { Button } from "@/components/ui/button"
import { Settings, ArrowLeft } from "lucide-react"
import Link from "next/link"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ProjectDocuments } from "@/components/projects/project-documents"
import { ProjectAgents } from "@/components/projects/project-agents"
import { useParams } from "next/navigation"

export default function ProjectPage() {
    const params = useParams()
    console.log(params)
    const projectId = params.projectId as string

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      {/* Header */}
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div>
           <div className="flex items-center gap-2 mb-2">
                <Button variant="ghost" size="sm" asChild className="-ml-3 text-muted-foreground">
                    <Link href="/projects">
                        <ArrowLeft className="mr-2 h-4 w-4" /> Back to Projects
                    </Link>
                </Button>
           </div>
          <h2 className="text-3xl font-bold tracking-tight">Legal Contract Analysis</h2>
          <p className="text-muted-foreground mt-2">
            Project configuration and knowledge base. 
            {/* TODO: Fetch real project name */}
          </p>
        </div>
        <div className="flex items-center gap-2">
            <Button variant="outline">
            <Settings className="mr-2 h-4 w-4" /> Settings
            </Button>
        </div>
      </div>

        {/* Main Content Tabs */}
      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="grid w-full grid-cols-3 lg:w-100">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="documents">Knowledge Base</TabsTrigger>
          <TabsTrigger value="agents">Agents</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="mt-6 space-y-6">
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                 <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="text-2xl font-bold">145</div>
                    <p className="text-xs text-muted-foreground">Total Documents</p>
                 </div>
                 <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="text-2xl font-bold">3</div>
                    <p className="text-xs text-muted-foreground">Active Agents</p>
                 </div>
                 <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="text-2xl font-bold">1,234</div>
                    <p className="text-xs text-muted-foreground">Total Vector Chunks</p>
                 </div>
                 <div className="rounded-xl border bg-card text-card-foreground shadow p-6">
                    <div className="text-2xl font-bold">89%</div>
                    <p className="text-xs text-muted-foreground">Avg. Retrieval Score</p>
                 </div>
            </div>
            {/* Recent Activity or other widgets could go here */}
        </TabsContent>

        <TabsContent value="documents" className="mt-6">
            <ProjectDocuments projectId={projectId} />
        </TabsContent>

        <TabsContent value="agents" className="mt-6">
            <ProjectAgents projectId={projectId} />
        </TabsContent>
      </Tabs>
    </div>
  )
}
