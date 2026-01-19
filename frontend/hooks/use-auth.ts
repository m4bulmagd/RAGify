"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { apiFetch } from "@/lib/api"

interface User {
  id: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
}

export function useAuth() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchUser = async () => {
      try {
        const res = await apiFetch("/users/me")

        if (res.ok) {
          const data = await res.json()
          setUser(data)
        } else if (res.status === 401 || res.status === 403) {
          // Unauthorized - cookie expired/invalid
          setUser(null)
        } else {
          // Network or server error - don't auto-logout
          console.error("Failed to verify user:", res.status)
          // Optionally: retry or show error toast
        }
      } catch (error) {
        // Network failure - don't logout, might be temporary
        console.error("Network error fetching user", error)
      } finally {
        setLoading(false)
      }
    }

    fetchUser()
  }, [])

  const logout = async () => {
    try {
      await apiFetch("/login/logout", {
        method: "POST",
      })
    } catch (e) {
      console.error("Logout failed", e)
    }
    setUser(null)
    router.push("/login")
  }

  return { user, loading, logout }
}
