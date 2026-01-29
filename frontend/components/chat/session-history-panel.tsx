"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

type Session = {
  id: number
  topic: string
  level: string
  created_at: string
  iterations_count: number
  status: "active" | "completed"
}

type SessionHistoryPanelProps = {
  onNewSession?: () => void
  onSelectSession?: (sessionId: number) => void
}

export function SessionHistoryPanel({
  onNewSession,
  onSelectSession,
}: SessionHistoryPanelProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchSessions()
  }, [])

  const fetchSessions = async () => {
    try {
      setLoading(true)
      const token = localStorage.getItem("access_token")
      
      if (!token) {
        setError("Not authenticated")
        return
      }

      const response = await fetch("http://localhost:8000/api/v1/sessions", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error("Failed to fetch sessions")
      }

      const data = await response.json()
      setSessions(data.sessions || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error")
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <Card className="border-border/60 bg-card/60">
      <CardHeader>
        <CardTitle className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
          Sessions
        </CardTitle>
        <CardDescription className="text-xs">
          Your learning sessions history
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-2">
        <Button
          variant="secondary"
          className="w-full"
          onClick={onNewSession}
        >
          + New session
        </Button>

        {loading && (
          <div className="rounded-lg border border-border/60 bg-background/30 p-3 text-xs text-muted-foreground">
            Loading sessions...
          </div>
        )}

        {error && (
          <div className="rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
            {error}
          </div>
        )}

        {!loading && !error && sessions.length === 0 && (
          <div className="rounded-lg border border-border/60 bg-background/30 p-3 text-xs text-muted-foreground">
            No sessions yet. Create your first one!
          </div>
        )}

        {!loading && !error && sessions.length > 0 && (
          <div className="space-y-2 max-h-[400px] overflow-y-auto">
            {sessions.slice(0, 10).map((session) => (
              <button
                key={session.id}
                onClick={() => onSelectSession?.(session.id)}
                className="w-full text-left rounded-lg border border-border/60 bg-background/30 p-3 hover:bg-background/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-medium text-foreground truncate">
                      {session.topic}
                    </div>
                    <div className="text-[10px] text-muted-foreground mt-0.5">
                      {session.iterations_count} iterations · {formatDate(session.created_at)}
                    </div>
                  </div>
                  <Badge
                    variant={session.status === "active" ? "default" : "secondary"}
                    className="text-[10px] px-1.5 py-0.5 shrink-0"
                  >
                    {session.level}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

