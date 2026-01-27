"use client"

import { useEffect, useRef } from "react"
import { toast } from "sonner"
import { useQueryClient } from "@tanstack/react-query"

// Use a singleton-like pattern to avoid multiple connections if hook is used multiple times
let socket: WebSocket | null = null
let subscribers = 0

export function useSocket() {
  const queryClient = useQueryClient()
  const socketRef = useRef<WebSocket | null>(null)

  useEffect(() => {
    // Simple reconnect logic could be added here
    const connect = () => {
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
      // Assuming backend runs on port 8000 for local dev or /api/v1/ws via proxy
      // Adjust URL based on env
      const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}/api/v1/ws`
      
      if (!socket || socket.readyState === WebSocket.CLOSED) {
          socket = new WebSocket(wsUrl)
          
          socket.onopen = () => {
              console.log("WebSocket connected")
          }
          
          socket.onmessage = (event) => {
              try {
                  const data = JSON.parse(event.data)
                  handleMessage(data)
              } catch (e) {
                  console.error("WS Parse error", e)
              }
          }
          
          socket.onclose = () => {
              console.log("WebSocket disconnected")
              // socket = null // Allow reconnect attempts?
          }
      }
      subscribers++
    }

    const handleMessage = (data: any) => {
        if (data.type === "document_status") {
            const { document_id, status, message } = data
            
            // Invalidate queries to refresh lists
            queryClient.invalidateQueries({ queryKey: ["documents"] })
            queryClient.invalidateQueries({ queryKey: ["dashboard-stats"] })
            
            if (status === "completed") {
                toast.success("Document processed", {
                    description: message || "Ready for retrieval"
                })
            } else if (status === "failed") {
                toast.error("Processing failed", {
                    description: message
                })
            }
        }
    }

    connect()

    return () => {
        subscribers--
        if (subscribers === 0 && socket) {
            socket.close()
            socket = null
        }
    }
  }, [queryClient])
}
