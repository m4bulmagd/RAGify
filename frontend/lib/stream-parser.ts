export interface StreamEvent {
  type: "citation" | "content" | "usage" | "error" | "done"
  data: any
}

export async function* parseSSEStream(response: Response): AsyncGenerator<StreamEvent, void, unknown> {
  if (!response.body) throw new Error("No response body")

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split("\n\n")
      
      // Keep the last part if incomplete
      buffer = lines.pop() || ""

      for (const line of lines) {
        if (line.startsWith("data: ")) {
          const jsonStr = line.slice(6)
          if (jsonStr.trim() === "[DONE]") continue
          
          try {
            const event = JSON.parse(jsonStr)
            yield event
          } catch (e) {
            console.warn("Failed to parse SSE JSON:", jsonStr, e)
          }
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}