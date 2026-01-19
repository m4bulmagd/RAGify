"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Bot, Loader2 } from "lucide-react"

export default function RegisterPage() {
  const router = useRouter()
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError("")

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/users/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          password,
          full_name: `${firstName} ${lastName}`.trim(),
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.detail || "Registration failed")
      }

      router.push("/login")
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <Card className="w-full max-w-md border-primary/20 shadow-2xl">
      <CardHeader className="space-y-1 flex flex-col items-center text-center">
        <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center mb-2 animate-pulse-slow">
           <Bot className="h-6 w-6 text-primary" />
        </div>
        <CardTitle className="text-2xl font-bold tracking-tight">Create an account</CardTitle>
        <CardDescription>
          Enter your email below to create your account
        </CardDescription>
      </CardHeader>
      <form onSubmit={handleRegister}>
        <CardContent className="space-y-4">
          {error && <div className="text-red-500 text-sm text-center">{error}</div>}
          <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                  <Label htmlFor="first-name">First name</Label>
                  <Input 
                    id="first-name" 
                    placeholder="John" 
                    className="bg-background/50 border-primary/20 focus:border-primary transition-all"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                  />
              </div>
              <div className="space-y-2">
                  <Label htmlFor="last-name">Last name</Label>
                  <Input 
                    id="last-name" 
                    placeholder="Doe" 
                    className="bg-background/50 border-primary/20 focus:border-primary transition-all"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                  />
              </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input 
              id="email" 
              placeholder="name@example.com" 
              type="email" 
              className="bg-background/50 border-primary/20 focus:border-primary transition-all"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input 
              id="password" 
              type="password" 
              className="bg-background/50 border-primary/20 focus:border-primary transition-all"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <Button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground shadow-lg" disabled={loading}>
            {loading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Create account"}
          </Button>
        </CardContent>
      </form>
      <CardFooter className="flex justify-center">
        <p className="text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="text-primary hover:underline">
            Sign in
          </Link>
        </p>
      </CardFooter>
    </Card>
  )
}
