"use client"

import {
  Calendar,
  ChevronRight,
  Clock,
  MessageSquare,
  Plus,
  Terminal,
} from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"

import { fetchSessions } from "@/lib/sessions"
import type { SessionSummary } from "@/types/session"

export default function SessionsPage() {
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const data = await fetchSessions()
        setSessions(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load sessions")
      } finally {
        setLoading(false)
      }
    }

    loadSessions()
  }, [])

  const handleNewSession = () => {
    router.push("/chat")
  }

  const handleSessionClick = (sessionId: number) => {
    router.push(`/chat?session=${sessionId}`)
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-orange-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-blue-900/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[400px] w-[400px] rounded-full bg-orange-900/5 blur-[100px]" />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.02]" />
      </div>

      {/* Header */}
      <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#050505]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <Link href="/" className="flex items-center gap-3 group">
            <div className="size-1.5 animate-pulse rounded-full bg-orange-500 shadow-[0_0_8px_currentColor] transition-transform group-hover:scale-125" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-white/70 transition-colors group-hover:text-white">
              Claude Tests
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <Link 
              href="/chat"
              className="text-xs font-medium text-white/50 transition-colors hover:text-white"
            >
              Current Session
            </Link>
            <button className="text-xs font-medium text-white/50 transition-colors hover:text-white">Export</button>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-4xl px-6 pb-24 pt-32">
        <div className="mb-12 flex items-end justify-between">
          <div>
            <h1 className="text-3xl font-bold uppercase tracking-tight md:text-4xl">
              Session <span className="text-orange-500">Log</span>
            </h1>
            <p className="mt-2 text-sm text-white/40">
              Access previous cognitive interrogation records.
            </p>
          </div>
          
          <button
            onClick={handleNewSession}
            className="group flex items-center gap-2 rounded-full bg-white/5 px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-white transition-all hover:bg-white/10 hover:shadow-[0_0_20px_rgba(255,255,255,0.1)]"
          >
            <Plus className="size-3 transition-transform group-hover:rotate-90" />
            New Session
          </button>
        </div>

        {loading ? (
          <div className="flex h-64 items-center justify-center gap-3 text-sm text-white/40">
            <Clock className="size-4 animate-spin" />
            RETRIEVING LOGS...
          </div>
        ) : error ? (
          <div className="flex h-64 items-center justify-center text-sm text-red-400">
            ERROR: {error}
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center rounded-2xl border border-white/5 bg-white/[0.02] py-20 text-center backdrop-blur-sm">
            <Terminal className="mb-4 size-12 text-white/10" />
            <h3 className="mb-2 text-lg font-bold text-white/50">No Records Found</h3>
            <p className="mb-8 text-sm text-white/30">Begin your first interrogation sequence.</p>
            <button
              onClick={handleNewSession}
              className="rounded-full bg-orange-600 px-8 py-3 text-xs font-bold uppercase tracking-wider text-white shadow-[0_0_20px_rgba(234,88,12,0.3)] transition-transform hover:scale-105 hover:bg-orange-500"
            >
              Initialize Session
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {sessions.map((session, i) => (
              <motion.div
                key={session.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                onClick={() => handleSessionClick(session.id)}
                className="group relative cursor-pointer overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] p-6 transition-all hover:border-orange-500/30 hover:bg-white/[0.04]"
              >
                {/* Glow on hover */}
                <div className="absolute -right-12 -top-12 size-24 rounded-full bg-orange-500/0 blur-2xl transition-colors group-hover:bg-orange-500/10" />

                <div className="relative z-10 flex items-start justify-between gap-4">
                  <div className="space-y-1">
                    <div className="flex items-center gap-2 mb-2">
                       <span className="text-[10px] font-bold uppercase tracking-widest text-white/30">
                         ID: {String(session.id).padStart(4, '0')}
                       </span>
                       <div className="h-px w-4 bg-white/10" />
                       <span className={`text-[10px] font-bold uppercase tracking-widest ${session.status === 'active' ? 'text-green-400' : 'text-white/30'}`}>
                         {session.status}
                       </span>
                    </div>
                    <h3 className="text-lg font-bold text-white group-hover:text-orange-400 transition-colors">
                      {session.topic || "Untitled Session"}
                    </h3>
                    <div className="flex items-center gap-3 text-xs text-white/40">
                      {session.level && (
                        <span className="rounded-full border border-white/10 px-2 py-0.5 uppercase tracking-wide">
                          {session.level}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <MessageSquare className="size-3" />
                        {session.iteration_count} msgs
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-4">
                    <span className="text-[10px] font-mono text-white/30 group-hover:text-white/50 transition-colors">
                      {formatDate(session.updated_at)}
                    </span>
                    <div className="rounded-full bg-white/5 p-2 text-white/30 transition-colors group-hover:bg-orange-500/20 group-hover:text-orange-500">
                      <ChevronRight className="size-4" />
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
