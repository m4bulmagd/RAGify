export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const headers = new Headers(options.headers)

  if (options.body instanceof FormData) {
     // Let browser set content-type with boundary
  } else {
     headers.set("Content-Type", "application/json")
  }

  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers,
  })

  if (res.status === 401) {
    // Redirect to login on auth failure
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }

  return res
}