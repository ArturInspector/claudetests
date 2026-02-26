"use client"

import { create } from "zustand"

import { AuthUser, clearToken, fetchProfile, getStoredToken } from "@/lib/auth"

type AuthState = {
  user: AuthUser | null
  token: string | null
  status: "idle" | "loading"
  error: string | null
  setAuth: (token: string, user: AuthUser) => void
  hydrate: () => Promise<void>
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  status: "idle",
  error: null,
  setAuth: (token, user) => set({ token, user, status: "idle", error: null }),
  hydrate: async () => {
    const token = getStoredToken()
    if (!token) return

    set({ status: "loading", error: null })
    try {
      const user = await fetchProfile(token)
      set({ user, token, status: "idle" })
    } catch (error) {
      clearToken()
      set({
        user: null,
        token: null,
        status: "idle",
        error: error instanceof Error ? error.message : "Unable to load session",
      })
    }
  },
  logout: () => {
    clearToken()
    set({ user: null, token: null, status: "idle", error: null })
  },
}))











