export async function apiFetch(endpoint: string, options: RequestInit = {}) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  if (res.status === 401) {
    // Redirect to login on auth failure
    window.location.href = "/login"
    throw new Error("Unauthorized")
  }

  return res
}