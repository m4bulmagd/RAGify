import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Bot } from "lucide-react"

export default function LoginPage() {
  return (
    <Card className="w-full max-w-md border-primary/20 shadow-2xl">
      <CardHeader className="space-y-1 flex flex-col items-center text-center">
        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mb-2 animate-pulse-slow">
           <Bot className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-2xl font-bold tracking-tight">Welcome back</CardTitle>
        <CardDescription>
          Enter your email to sign in to your RAGify account
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input id="email" placeholder="name@example.com" type="email" className="bg-background/50 border-primary/20 focus:border-primary transition-all" />
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label htmlFor="password">Password</Label>
            <Link href="#" className="text-xs text-primary hover:underline">
              Forgot password?
            </Link>
          </div>
          <Input id="password" type="password" className="bg-background/50 border-primary/20 focus:border-primary transition-all" />
        </div>
        <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg">
          Sign In
        </Button>
      </CardContent>
      <CardFooter className="flex justify-center">
        <p className="text-sm text-muted-foreground">
          Don't have an account?{" "}
          <Link href="/register" className="text-primary hover:underline">
            Sign up
          </Link>
        </p>
      </CardFooter>
    </Card>
  )
}
