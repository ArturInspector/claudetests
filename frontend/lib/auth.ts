"use client"

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1"
const TOKEN_KEY = "access_token"

export type AuthUser = {
  id: number
  email: string
}

type TokenResponse = {
  access_token: string
  token_type: string
}

type RegisterResponse = TokenResponse & {
  user: AuthUser
}

const parseError = async (response: Response) => {
  try {
    const data = await response.json()
    return typeof data.detail === "string"
      ? data.detail
      : data.detail?.[0]?.msg || "Request failed"
  } catch {
    return "Request failed"
  }
}

export const persistToken = (token: string) => {
  if (typeof window === "undefined") return

  localStorage.setItem(TOKEN_KEY, token)
  document.cookie = `access_token=${token}; Path=/; Max-Age=604800; SameSite=Lax`
}

export const clearToken = () => {
  if (typeof window === "undefined") return

  localStorage.removeItem(TOKEN_KEY)
  document.cookie = `access_token=; Path=/; Max-Age=0; SameSite=Lax`
}

export const getStoredToken = () => {
  if (typeof window === "undefined") return null
  return localStorage.getItem(TOKEN_KEY)
}

export const fetchProfile = async (token?: string): Promise<AuthUser> => {
  const bearer = token ?? getStoredToken()
  if (!bearer) {
    throw new Error("Missing token")
  }

  const res = await fetch(`${API_BASE}/auth/me`, {
    headers: {
      Authorization: `Bearer ${bearer}`,
    },
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error(await parseError(res))
  }

  return res.json()
}

export const login = async (payload: {
  email: string
  password: string
}) => {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error(await parseError(res))
  }

  const data: TokenResponse = await res.json()
  persistToken(data.access_token)
  const user = await fetchProfile(data.access_token)

  return { token: data.access_token, user }
}

export const register = async (payload: {
  email: string
  password: string
}) => {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  })

  if (!res.ok) {
    throw new Error(await parseError(res))
  }

  const data: RegisterResponse = await res.json()
  persistToken(data.access_token)

  return { token: data.access_token, user: data.user }
}

