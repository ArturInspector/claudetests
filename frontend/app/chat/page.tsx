"use client"

import { AnimatePresence, motion } from "framer-motion"
import {
  Activity,
  ArrowRight,
  Brain,
  ChevronDown,
  ChevronUp,
  Clock,
  Command,
  Cpu,
  History,
  Lightbulb,
  LogOut,
  MessageSquare,
  Send,
  Sparkles,
  Terminal,
  Zap,
} from "lucide-react"
import Link from "next/link"
import { useRouter, useSearchParams } from "next/navigation"
import { useEffect, useMemo, useRef, useState } from "react"

import { createSession, fetchSessionMessages } from "@/lib/sessions"
import { useAuthStore } from "@/stores/auth"
import type { Gap, KnowledgeHint, Message, SocraticMove } from "@/types/chat"
import type { SessionDetail } from "@/types/session"

// --- Types & Constants ---

const QUESTION = {
  title: "What is partition tolerance in the CAP theorem?",
  prompt:
    "Explain how partition tolerance influences consistency and availability trade-offs. Include one example from a real-world system.",
  difficulty: "Intermediate" as const,
  topic: "Distributed systems",
}

type Mode = "practice" | "interview"

// --- Helper Components ---

const GlowBadge = ({ children, color = "blue" }: { children: React.ReactNode; color?: "blue" | "orange" | "green" }) => {
  const colors = {
    blue: "bg-blue-500/10 text-blue-400 border-blue-500/20 shadow-[0_0_10px_rgba(59,130,246,0.1)]",
    orange: "bg-orange-500/10 text-orange-400 border-orange-500/20 shadow-[0_0_10px_rgba(249,115,22,0.1)]",
    green: "bg-green-500/10 text-green-400 border-green-500/20 shadow-[0_0_10px_rgba(34,197,94,0.1)]",
  }

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-medium uppercase tracking-wider ${colors[color]}`}
    >
      <span className={`size-1.5 rounded-full ${color === "blue" ? "bg-blue-400" : color === "orange" ? "bg-orange-400" : "bg-green-400"} shadow-[0_0_5px_currentColor]`} />
      {children}
    </span>
  )
}

const GlassPanel = ({ children, className = "", hover = false }: { children: React.ReactNode; className?: string; hover?: boolean }) => (
  <div
    className={`relative overflow-hidden rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-xl ${
      hover ? "transition-all duration-300 hover:border-white/10 hover:bg-white/[0.04] hover:shadow-[0_0_30px_rgba(255,255,255,0.02)]" : ""
    } ${className}`}
  >
    {children}
  </div>
)

const ProgressBar = ({ label, value, color = "bg-blue-500" }: { label: string; value: number; color?: string }) => (
  <div className="group space-y-1.5">
    <div className="flex items-center justify-between text-[10px] font-medium uppercase tracking-wider text-white/40">
      <span>{label}</span>
      <span className="opacity-0 transition-opacity group-hover:opacity-100">{value}%</span>
    </div>
    <div className="h-1 w-full overflow-hidden rounded-full bg-white/5">
      <motion.div
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 1, ease: "easeOut" }}
        className={`h-full ${color} shadow-[0_0_10px_currentColor]`}
      />
    </div>
  </div>
)

// --- Main Page Component ---

export default function ChatPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionIdParam = searchParams.get("session")
  const logout = useAuthStore((state) => state.logout)

  const [sessionId, setSessionId] = useState<number | null>(sessionIdParam ? parseInt(sessionIdParam) : null)
  const [sessionDetail, setSessionDetail] = useState<SessionDetail | null>(null)
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<Mode>("practice")
  const [secondsLeft, setSecondsLeft] = useState<number>(45 * 60)
  const [timerRunning, setTimerRunning] = useState(false)
  const [loadingSession, setLoadingSession] = useState(false)
  const [showHistory, setShowHistory] = useState(false)

  const initialQuestionMessage = useMemo<Message>(
    () => ({
      id: "question-1",
      role: "assistant",
      content: QUESTION.prompt,
      timestamp: new Date(),
      metadata: {
        question: {
          title: QUESTION.title,
          difficulty: QUESTION.difficulty,
          topic: QUESTION.topic,
          prompt: QUESTION.prompt,
        },
      },
    }),
    []
  )

  const [messages, setMessages] = useState<Message[]>([initialQuestionMessage])
  const scrollRef = useRef<HTMLDivElement>(null)

  // --- Logic from original file ---

  useEffect(() => {
    const loadSession = async () => {
      if (!sessionId) return

      setLoadingSession(true)
      try {
        const detail = await fetchSessionMessages(sessionId)
        setSessionDetail(detail)

        if (detail.iterations.length > 0) {
          const loadedMessages: Message[] = [initialQuestionMessage]

          detail.iterations.forEach((iter) => {
            loadedMessages.push({
              id: `user-${iter.id}`,
              role: "user",
              content: iter.answer,
              timestamp: new Date(iter.created_at),
            })

            if (iter.feedback) {
              loadedMessages.push({
                id: `assistant-${iter.id}`,
                role: "assistant",
                content: iter.feedback,
                timestamp: new Date(iter.created_at),
              })
            }
          })

          setMessages(loadedMessages)
        }
      } catch (err) {
        console.error("Failed to load session:", err)
      } finally {
        setLoadingSession(false)
      }
    }

    loadSession()
  }, [sessionId, initialQuestionMessage])

  useEffect(() => {
    if (!timerRunning) return
    const id = setInterval(() => {
      setSecondsLeft((prev) => {
        if (prev <= 1) {
          setTimerRunning(false)
          return 0
        }
        return prev - 1
      })
    }, 1000)
    return () => clearInterval(id)
  }, [timerRunning])

  const evaluateAnswer = (answer: string) => {
    const normalized = answer.toLowerCase()
    const hasPartition = normalized.includes("partition")
    const hasTradeoff = normalized.includes("trade-off") || normalized.includes("tradeoff") || normalized.includes("однако")
    const hasExample = normalized.includes("например") || normalized.includes("e.g.") || normalized.includes("dynamo") || normalized.includes("mongo")
    const hasNumbers = /\d+/.test(answer)
    const lengthScore = Math.min(1, answer.length / 500)
    const includesPacelc = normalized.includes("pacelc")
    const mentionsRaft = normalized.includes("raft") || normalized.includes("paxos")

    const gaps: Gap[] = []
    if (!hasPartition) gaps.push({ label: "Опиши, что такое сетевой partition", done: false, hint: "Разрыв связности между нодами" })
    if (!hasTradeoff) gaps.push({ label: "Отрази CAP trade-off", done: false, hint: "Связь consistency vs availability" })
    if (!hasExample) gaps.push({ label: "Приведи реальный пример", done: false, hint: "Dynamo, MongoDB, Kafka" })

    const base = 0.3 + lengthScore * 0.3 + (hasTradeoff ? 0.2 : 0) + (hasExample ? 0.1 : 0) + (hasNumbers ? 0.1 : 0)
    const understanding = Math.min(1, base)
    const confidence = Math.min(1, 0.25 + lengthScore * 0.5 + (hasNumbers ? 0.1 : 0) + (mode === "interview" ? 0.05 : 0))

    const moves: SocraticMove[] = []
    if (!hasTradeoff) {
      moves.push({
        type: "probe",
        text: "Как CAP влияет на выбор между консистентностью и доступностью в реальном инциденте?",
        rationale: "Уточнить понимание ключевого trade-off",
        difficulty: "intermediate",
      })
    }
    if (hasPartition && !hasExample) {
      moves.push({
        type: "challenge",
        text: "Приведи конкретный кейс из продакшена, где partition сломал систему. Что бы ты сделал иначе?",
        difficulty: "advanced",
      })
    }
    if (understanding > 0.6) {
      moves.push({
        type: "extend",
        text: "Сравни CAP и PACELC: как latency меняет выбор?",
        difficulty: "advanced",
      })
    } else {
      moves.push({
        type: "simplify",
        text: "Опиши CAP как для менеджера без техбэкграунда за 2 предложения.",
        difficulty: "beginner",
      })
    }

    const graphHints: KnowledgeHint[] = []
    if (!hasPartition) graphHints.push({ concept: "Partition Tolerance", status: "unexplored", action: "Разобрать сценарий split-brain" })
    if (!hasTradeoff) graphHints.push({ concept: "Consistency vs Availability", status: "weak", action: "Пример AP и CP" })
    if (hasExample && hasTradeoff) graphHints.push({ concept: "PACELC", status: "solid", action: "Сравнить с CAP" })
    if (mentionsRaft) graphHints.push({ concept: "Consensus (Raft/Paxos)", status: "weak", action: "Связать с CAP" })

    const misconceptions = []
    if (!hasPartition) {
      misconceptions.push({ label: "CAP без partition — неполное определение", correction: "Partition tolerance обязательна" })
    }
    if (normalized.includes("choose two")) {
      misconceptions.push({
        label: "CAP не про выбор любых двух свойств",
        correction: "Partition считается данностью, выбор — между C и A при P",
      })
    }
    if (includesPacelc && !hasTradeoff) {
      misconceptions.push({
        label: "Упомянут PACELC без явного trade-off",
        correction: "PACELC добавляет latency trade-off к CAP, укажи L",
      })
    }

    return {
      understanding,
      confidence,
      gaps,
      misconceptions,
      notes: understanding > 0.7 ? "Хорошо! Давай углубимся в PACELC." : "Нужно связать partition с выбором CA.",
      nextDifficulty: (understanding > 0.7 ? "advanced" : "intermediate") as "beginner" | "intermediate" | "advanced",
      socraticMoves: moves,
      graphHints,
    }
  }

  const getAccessToken = () => {
    if (typeof window === "undefined") return null
    const storeToken = useAuthStore.getState().token
    if (storeToken) return storeToken
    const lsToken = localStorage.getItem("access_token")
    if (lsToken) return lsToken
    const cookieMatch = document.cookie.match(/(?:^|; )access_token=([^;]+)/)
    return cookieMatch ? decodeURIComponent(cookieMatch[1]) : null
  }

  const fetchAnalysis = async (answer: string, currentSessionId: number | null) => {
    const token = getAccessToken()
    if (!token) return null
    try {
      const resp = await fetch("http://localhost:8000/api/v1/socratic/analyze", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          question: QUESTION.prompt,
          answer,
          topic: QUESTION.topic,
          mode,
          required_terms: ["partition", "consistency", "availability"],
          session_id: currentSessionId ? String(currentSessionId) : undefined,
        }),
      })
      if (!resp.ok) return null
      return (await resp.json()) as any
    } catch (err) {
      console.warn("socratic analyze fallback to local", err)
      return null
    }
  }

  const handleSend = async () => {
    if (!input.trim() || loading) return
    const content = input.trim()
    setInput("")
    if (mode === "interview") setTimerRunning(true)

    const userMessage: Message = {
      id: crypto.randomUUID(),
      role: "user",
      content,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, userMessage])
    setLoading(true)

    try {
      let currentSessionId = sessionId

      if (!currentSessionId) {
        const newSession = await createSession({
          topic: QUESTION.topic,
          level: QUESTION.difficulty,
        })
        currentSessionId = newSession.id
        setSessionId(currentSessionId)
        setSessionDetail(newSession)
        router.push(`/chat?session=${currentSessionId}`, { scroll: false })
      }

      await new Promise((resolve) => setTimeout(resolve, 350))

      const remote = await fetchAnalysis(content, currentSessionId)
      const local = evaluateAnswer(content)
      const analysis = remote?.analysis
        ? {
            understanding: remote.analysis.understanding ?? local.understanding,
            confidence: remote.analysis.confidence ?? local.confidence,
            gaps: local.gaps,
            notes: local.notes,
            misconceptions: remote.analysis.misconceptions ?? local.misconceptions,
            nextDifficulty: remote.analysis.nextDifficulty ?? local.nextDifficulty,
          }
        : local
      const socratic = remote?.socratic ?? { moves: local.socraticMoves, next_step: local.notes }
      const graph = remote?.graph ?? { hints: local.graphHints }
      const selectedQuestion =
        socratic.selected_question ||
        socratic.moves?.[0]?.text ||
        local.socraticMoves?.[0]?.text ||
        "Уточни свой ответ."
      const assistantMessage: Message = {
        id: crypto.randomUUID(),
        role: "assistant",
        content: selectedQuestion,
        timestamp: new Date(),
        metadata: {
          analysis: {
            understanding: analysis.understanding,
            confidence: analysis.confidence,
            gaps: analysis.gaps,
            notes: analysis.notes,
            misconceptions: analysis.misconceptions,
            nextDifficulty: analysis.nextDifficulty,
          },
          socratic: {
            moves: socratic.moves ?? local.socraticMoves,
            nextStep: socratic.next_step,
            selected_question: socratic.selected_question ?? selectedQuestion,
            selection_rationale: socratic.selection_rationale,
          },
          graph: {
            hints: graph?.hints ?? local.graphHints,
          },
        },
      }

      setMessages((prev) => [...prev, assistantMessage])
    } catch (err) {
      console.error("Error handling send:", err)
    } finally {
      setLoading(false)
    }
  }

  const handleLogout = () => {
    logout()
    router.replace("/login")
  }

  const activeQuestion = messages.filter((m) => m.role === "assistant").pop() || initialQuestionMessage
  const history = messages.slice(0, -1) // All except current (active) question? 
  // Wait, if last is USER (loading), then active is still the previous assistant msg?
  // Let's refine:
  // If loading: active is "Analyzing..." or keep previous? 
  // Socratic: User answers Q1. Loading. Then AI gives Q2.
  // While loading, user wants to see their answer.
  
  // Logic: 
  // - Main Panel always shows the LATEST ASSISTANT MESSAGE.
  // - History shows everything before that.
  
  let latestAssistantIndex = -1
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].role === "assistant") {
      latestAssistantIndex = i
      break
    }
  }

  const mainQuestion = messages[latestAssistantIndex] || initialQuestionMessage
  const conversationHistory = latestAssistantIndex > 0 ? messages.slice(0, latestAssistantIndex) : []
  const pendingUserMessage = messages.length > latestAssistantIndex + 1 ? messages[messages.length - 1] : null

  return (
    <div className="min-h-screen bg-[#050505] text-white selection:bg-orange-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 h-[500px] w-[500px] -translate-x-1/2 rounded-full bg-blue-900/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[400px] w-[400px] rounded-full bg-orange-900/5 blur-[100px]" />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.02]" />
      </div>

      {/* --- 1) TOP BAR --- */}
      <header className="fixed top-0 z-50 w-full border-b border-white/5 bg-[#050505]/80 backdrop-blur-md">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="size-1.5 animate-pulse rounded-full bg-orange-500 shadow-[0_0_8px_currentColor]" />
            <span className="text-xs font-bold uppercase tracking-[0.2em] text-white/70">Claude Tests</span>
          </div>

          <div className="hidden items-center gap-4 md:flex">
            <div className="flex items-center gap-2 rounded-full border border-white/5 bg-white/5 px-4 py-1.5">
              <span className="text-xs text-white/50">{sessionDetail?.topic || QUESTION.topic}</span>
              <div className="h-3 w-px bg-white/10" />
              <GlowBadge color="orange">{sessionDetail?.level || QUESTION.difficulty}</GlowBadge>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <button 
              onClick={() => router.push("/sessions")}
              className="text-xs font-medium text-white/50 transition-colors hover:text-white"
            >
              Sessions
            </button>
            <button className="text-xs font-medium text-white/50 transition-colors hover:text-white">Export</button>
            <button 
              onClick={handleLogout}
              className="flex items-center gap-2 text-xs font-medium text-white/50 transition-colors hover:text-red-400"
            >
              <LogOut className="size-3" />
              Logout
            </button>
          </div>
        </div>
      </header>

      <main className="relative z-10 mx-auto max-w-4xl px-6 pb-24 pt-32">
        {loadingSession ? (
          <div className="flex h-[50vh] items-center justify-center gap-3 text-sm text-white/40">
            <Clock className="size-4 animate-spin" />
            INITIALIZING SESSION...
          </div>
        ) : (
          <div className="space-y-12">
            
            {/* History Toggle / Preview */}
            {conversationHistory.length > 0 && (
              <div className="relative">
                <button 
                  onClick={() => setShowHistory(!showHistory)}
                  className="group flex w-full items-center justify-between rounded-lg border border-white/5 bg-white/[0.02] px-4 py-3 text-xs text-white/40 transition-colors hover:border-white/10 hover:bg-white/5"
                >
                  <span className="flex items-center gap-2 uppercase tracking-wider">
                    <History className="size-3" />
                    Previous Exchange ({conversationHistory.length})
                  </span>
                  {showHistory ? <ChevronUp className="size-3" /> : <ChevronDown className="size-3" />}
                </button>
                
                <AnimatePresence>
                  {showHistory && (
                    <motion.div
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden"
                    >
                      <div className="mt-4 space-y-6 border-l border-white/5 pl-6">
                        {conversationHistory.map((msg, i) => (
                          <div key={msg.id} className="space-y-2">
                            <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-white/30">
                              {msg.role === "assistant" ? <Brain className="size-3" /> : <Terminal className="size-3" />}
                              {msg.role}
                            </div>
                            <div className={`text-sm leading-relaxed ${msg.role === "assistant" ? "text-white/80" : "text-white/60 font-mono"}`}>
                              {msg.content}
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            )}

            {/* --- 2) MAIN INTERROGATION PANEL --- */}
            <motion.div
              key={mainQuestion.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <GlassPanel className="p-8 md:p-10" hover>
                {/* Glow Orb */}
                <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-blue-500/10 blur-[80px]" />

                <div className="relative z-10 space-y-6">
                  <div className="flex items-center justify-between border-b border-white/5 pb-4">
                    <div className="flex items-center gap-2 text-[10px] font-bold uppercase tracking-[0.2em] text-blue-400">
                      <Activity className="size-3" />
                      Assistant Protocol
                    </div>
                    <span className="text-[10px] text-white/30">{mainQuestion.timestamp.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                  </div>

                  <div className="space-y-4">
                    <h2 className="text-2xl font-bold tracking-tight leading-snug text-white md:text-3xl lg:text-4xl">
                      {mainQuestion.metadata?.question?.title || mainQuestion.content}
                    </h2>
                    
                    <div className="flex items-center gap-3">
                      <GlowBadge color="blue">
                        {mainQuestion.metadata?.question?.difficulty || "Adaptive"}
                      </GlowBadge>
                      <span className="text-xs text-white/30">
                        {mainQuestion.metadata?.question?.topic || "Topic Analysis"}
                      </span>
                    </div>
                  </div>

                  {mainQuestion.metadata?.question?.title && (
                     <div className="mt-8 rounded-lg border border-white/5 bg-black/20 p-4 text-sm text-white/50">
                        <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-white/30">
                          <Terminal className="size-3" />
                          Instruction
                        </div>
                        {mainQuestion.content}
                     </div>
                  )}

                  {/* Hints / Socratic Moves (if available in metadata) */}
                  {mainQuestion.metadata?.socratic?.moves && (
                    <div className="mt-6 flex flex-wrap gap-2 pt-4">
                       {mainQuestion.metadata.socratic.moves.map((move, i) => (
                         <span key={i} className="text-[10px] text-white/20 px-2 py-1 border border-white/5 rounded">
                           Strategy: {move.type}
                         </span>
                       ))}
                    </div>
                  )}
                </div>
              </GlassPanel>
            </motion.div>

            {/* --- 3) RESPONSE AREA --- */}
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 0.2 }}
               className="relative"
            >
              {pendingUserMessage && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mb-6 rounded-xl border border-white/5 bg-white/5 p-6 text-sm text-white/80"
                >
                  <div className="mb-2 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-white/30">
                    <Terminal className="size-3" />
                    Your Response
                  </div>
                  <div className="font-mono leading-relaxed">
                    {pendingUserMessage.content}
                  </div>
                </motion.div>
              )}

              <div className="mb-2 flex items-center justify-between px-2">
                 <span className="text-[10px] font-bold uppercase tracking-widest text-white/40">
                   Your Response
                 </span>
                 <div className="flex items-center gap-1.5 text-[10px] text-white/20">
                   <Command className="size-3" />
                   <span>Enter to submit</span>
                 </div>
              </div>

              <div className="group relative overflow-hidden rounded-xl bg-black border border-white/10 transition-colors focus-within:border-orange-500/50 hover:border-white/20">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                      handleSend()
                    }
                  }}
                  disabled={loading}
                  placeholder="Articulate your reasoning with clarity. Precision reveals understanding..."
                  className="min-h-[160px] w-full resize-none bg-transparent p-6 font-mono text-sm leading-relaxed text-white/90 placeholder:text-white/20 focus:outline-none disabled:opacity-50"
                  spellCheck={false}
                />
                
                {/* Pending User Message Display (if loading) */}
                {loading && (
                   <div className="absolute inset-0 z-10 flex flex-col items-center justify-center gap-3 bg-black/80 backdrop-blur-sm">
                      <div className="size-8 animate-spin rounded-full border-2 border-white/10 border-t-orange-500" />
                      <span className="text-xs font-medium uppercase tracking-widest text-orange-500 animate-pulse">Analyzing Response</span>
                   </div>
                )}

                <div className="absolute bottom-4 right-4">
                  <button
                    onClick={handleSend}
                    disabled={!input.trim() || loading}
                    className="group/btn flex items-center gap-2 rounded-lg bg-gradient-to-r from-orange-600 to-red-600 px-5 py-2.5 text-xs font-bold uppercase tracking-wider text-white shadow-lg transition-all hover:scale-105 hover:shadow-orange-500/20 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    Submit Analysis
                    <ArrowRight className="size-3 transition-transform group-hover/btn:translate-x-1" />
                  </button>
                </div>
              </div>
            </motion.div>

            {/* --- 4) COGNITIVE FEEDBACK (Placeholder) --- */}
            <motion.div 
               initial={{ opacity: 0 }}
               animate={{ opacity: 1 }}
               transition={{ delay: 0.4 }}
               className="rounded-xl border border-white/5 bg-white/[0.02] p-6"
            >
              <div className="mb-6 flex items-center gap-2 text-[10px] font-bold uppercase tracking-widest text-white/40">
                <Brain className="size-3" />
                Cognitive Evaluation Engine
              </div>
              
              <div className="grid gap-6 sm:grid-cols-2">
                <ProgressBar label="Depth of Reasoning" value={mainQuestion.metadata?.analysis?.understanding ? mainQuestion.metadata.analysis.understanding * 100 : 0} color="bg-blue-500" />
                <ProgressBar label="Structural Clarity" value={mainQuestion.metadata?.analysis?.confidence ? mainQuestion.metadata.analysis.confidence * 100 : 0} color="bg-purple-500" />
                <ProgressBar label="Conceptual Accuracy" value={0} color="bg-emerald-500" />
                <ProgressBar label="Knowledge Retention" value={0} color="bg-orange-500" />
              </div>
            </motion.div>
            
          </div>
        )}
      </main>
    </div>
  )
}
