import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { FileText, Bot, Settings, AlertCircle } from "lucide-react"

const activity = [
  {
    type: "upload",
    message: "Uploaded 'Q3_Financials.pdf'",
    project: "Financial Reports Q3",
    time: "2 mins ago",
    icon: FileText,
    color: "text-blue-500",
  },
  {
    type: "agent",
    message: "Updated system prompt",
    project: "Customer Support Bot",
    time: "1 hour ago",
    icon: Bot,
    color: "text-purple-500",
  },
  {
    type: "error",
    message: "Failed to process 'contract_v2.docx'",
    project: "Legal Contract Analysis",
    time: "3 hours ago",
    icon: AlertCircle,
    color: "text-red-500",
  },
  {
    type: "settings",
    message: "Changed retrieval threshold to 0.7",
    project: "HR Policy Helper",
    time: "5 hours ago",
    icon: Settings,
    color: "text-orange-500",
  },
  {
    type: "upload",
    message: "Uploaded 'employee_handbook.pdf'",
    project: "HR Policy Helper",
    time: "5 hours ago",
    icon: FileText,
    color: "text-blue-500",
  },
]

export function ActivityFeed() {
  return (
    <Card className="glass-card col-span-2 lg:col-span-1">
      <CardHeader>
        <CardTitle>Activity Feed</CardTitle>
        <CardDescription>
          Latest events across your workspace.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-6">
          {activity.map((item, i) => {
            const Icon = item.icon
            return (
              <div key={i} className="flex gap-4">
                <div className={`mt-0.5 rounded-full bg-background/50 p-1.5 ring-1 ring-border h-7 w-7 ${item.color}`}>
                  <Icon className="h-4 w-4" />
                </div>
                <div className="space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {item.message}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {item.project} • {item.time}
                  </p>
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
