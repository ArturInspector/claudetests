"use client"

import { ArrowRight, Lock, Mail, Terminal } from "lucide-react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { FormEvent, useState } from "react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { login } from "@/lib/auth"
import { useAuthStore } from "@/stores/auth"

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const next = searchParams.get("next") || "/chat"
  const setAuth = useAuthStore((state) => state.setAuth)

  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setLoading(true)

    try {
      const { token, user } = await login({ email, password })
      setAuth(token, user)
      router.replace(next)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to sign in")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-xl font-bold uppercase tracking-widest text-white">Authentication</h1>
        <p className="text-xs text-white/40">Enter credentials to access the testing matrix.</p>
      </div>

      <form className="space-y-4" onSubmit={handleSubmit}>
        <div className="space-y-1.5">
          <label className="text-[10px] font-bold uppercase tracking-wider text-white/30">Email Address</label>
          <div className="relative group">
            <Mail className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/20 transition-colors group-focus-within:text-orange-500" />
            <Input
              type="email"
              placeholder="operator@claudetests.ai"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
              className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-white/10 focus:border-orange-500/50 focus:bg-black/40 h-10 transition-all"
            />
          </div>
        </div>

        <div className="space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-[10px] font-bold uppercase tracking-wider text-white/30">Passkey</label>
            <Link href="#" className="text-[10px] text-white/30 hover:text-orange-400 transition-colors">
              Recover access?
            </Link>
          </div>
          <div className="relative group">
            <Lock className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-white/20 transition-colors group-focus-within:text-orange-500" />
            <Input
              type="password"
              placeholder="••••••••"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              className="pl-10 bg-black/20 border-white/10 text-white placeholder:text-white/10 focus:border-orange-500/50 focus:bg-black/40 h-10 transition-all"
            />
          </div>
        </div>

        {error && (
          <div className="flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-xs text-red-400">
            <Terminal className="size-3" />
            {error}
          </div>
        )}

        <Button 
          type="submit" 
          className="w-full bg-orange-600 hover:bg-orange-500 text-white font-bold uppercase tracking-wider h-10 shadow-[0_0_20px_rgba(234,88,12,0.2)] hover:shadow-[0_0_25px_rgba(234,88,12,0.4)] transition-all" 
          disabled={loading}
        >
          {loading ? "Authenticating..." : "Access System"}
          {!loading && <ArrowRight className="ml-2 size-3" />}
        </Button>

        <div className="mt-6 text-center text-xs text-white/30">
          New operator?{" "}
          <Link href="/register" className="text-orange-500 underline-offset-4 hover:text-orange-400 hover:underline transition-colors">
            Initialize profile
          </Link>
        </div>
      </form>
    </div>
  )
}
