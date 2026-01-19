"use client"

import * as React from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { 
  LayoutDashboard, 
  FolderOpen, 
  Settings, 
  CreditCard,
  Bot,
  LogOut
} from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"

const sidebarItems = [
  {
    title: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Projects",
    href: "/projects",
    icon: FolderOpen,
  },
  {
    title: "Agent Studio",
    href: "/agents",
    icon: Bot,
  },
  {
    title: "Usage & Billing",
    href: "/usage",
    icon: CreditCard,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
]

export function AppSidebar() {
  const pathname = usePathname()
  const { user, loading, logout } = useAuth()

  return (
    <div className="flex h-full w-64 flex-col border-r border-sidebar-border bg-sidebar-background text-sidebar-foreground">
      <div className="flex h-16 items-center border-b border-sidebar-border px-6">
        <div className="flex items-center gap-2 font-heading text-xl font-bold tracking-tight">
          <div className="h-6 w-6 rounded bg-primary" />
          RAGify
        </div>
      </div>
      <div className="flex-1 overflow-auto py-4">
        <nav className="grid gap-1 px-2">
          {sidebarItems.map((item, index) => {
            const Icon = item.icon
            const isActive = pathname === item.href || pathname.startsWith(item.href + "/")
            return (
              <Link
                key={index}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive 
                    ? "bg-sidebar-accent text-sidebar-accent-foreground bg-primary/20" 
                    : "hover:bg-primary/5 hover:text-primary"
                )}
              >
                <Icon className="h-4 w-4" />
                {item.title}
              </Link>
            )
          })}
        </nav>
      </div>
      <div className="border-t border-sidebar-border p-4">
        {loading ? (
           <div className="flex items-center gap-3 rounded-md bg-sidebar-accent p-3 animate-pulse">
             <div className="h-8 w-8 rounded-full bg-primary/10" />
             <div className="space-y-2">
                <div className="h-3 w-20 bg-primary/10 rounded" />
                <div className="h-2 w-32 bg-primary/10 rounded" />
             </div>
           </div>
        ) : user ? (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <div className="flex items-center gap-3 rounded-md bg-sidebar-accent p-3 cursor-pointer hover:bg-sidebar-accent/80 transition-colors">
                <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
                    <span className="text-xs font-bold text-primary">
                        {user.full_name?.charAt(0) || user.email.charAt(0).toUpperCase()}
                    </span>
                </div>
                <div className="text-sm flex-1 min-w-0">
                  <p className="font-medium truncate">{user.full_name || "User"}</p>
                  <p className="text-xs text-muted-foreground truncate">{user.email}</p>
                </div>
                <LogOut className="h-4 w-4 text-muted-foreground" />
              </div>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>My Account</DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={logout} className="text-red-500 focus:text-red-500 cursor-pointer">
                    <LogOut className="mr-2 h-4 w-4" />
                    <span>Log out</span>
                </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        ) : (
            <div className="p-3">
                <Link href="/login" className="text-sm font-medium hover:underline">
                    Sign in
                </Link>
            </div>
        )}
      </div>
    </div>
  )
}
