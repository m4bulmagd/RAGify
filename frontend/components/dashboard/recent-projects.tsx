import Link from "next/link"
import { ArrowRight, MoreHorizontal } from "lucide-react"

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

const data = [
  {
    id: "proj_1",
    name: "Legal Contract Analysis",
    description: "Analyzing NDAs and service agreements.",
    status: "active",
    docs: 145,
    updated: "2 mins ago",
  },
  {
    id: "proj_2",
    name: "Customer Support Bot",
    description: "RAG over Help Center articles.",
    status: "active",
    docs: 32,
    updated: "2 hours ago",
  },
  {
    id: "proj_3",
    name: "Financial Reports Q3",
    description: "Extraction from PDF balance sheets.",
    status: "archived",
    docs: 12,
    updated: "4 days ago",
  },
  {
    id: "proj_4",
    name: "HR Policy Helper",
    description: "Employee handbook Q&A.",
    status: "active",
    docs: 8,
    updated: "1 week ago",
  },
]

export function RecentProjects() {
  return (
    <Card className="col-span-3">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Recent Projects</CardTitle>
            <CardDescription>
              You have 3 active workspace projects.
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
        <div className="space-y-4">
          {data.map((project) => (
            <div
              key={project.id}
              className="flex items-center justify-between rounded-lg border border-border/50 bg-background/50 p-4 transition-all hover:bg-muted/50"
            >
              <div className="flex flex-col gap-1">
                <div className="flex items-center gap-2">
                  <span className="font-semibold">{project.name}</span>
                  <Badge variant={project.status === "active" ? "default" : "destructive"} className="text-[10px] uppercase">
                    {project.status}
                  </Badge>
                </div>
                <span className="text-sm text-muted-foreground">
                  {project.description}
                </span>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-right text-xs text-muted-foreground hidden sm:block">
                  <p>{project.docs} documents</p>
                  <p>Updated {project.updated}</p>
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="icon" className="h-8 w-8">
                      <MoreHorizontal className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    <DropdownMenuItem>View Project</DropdownMenuItem>
                    <DropdownMenuItem>Settings</DropdownMenuItem>
                    <DropdownMenuSeparator />
                    <DropdownMenuItem className="text-destructive">
                      Delete
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
