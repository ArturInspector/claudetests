"use client"

import { useEffect, useMemo, useState } from "react"

import { ChatInput } from "@/components/chat/chat-input"
import { MessageList } from "@/components/chat/message-list"
import type { Gap, KnowledgeHint, Message, SocraticMove } from "@/types/chat"

const QUESTION = {
  title: "What is partition tolerance in the CAP theorem?",
  prompt:
    "Explain how partition tolerance influences consistency and availability trade-offs. Include one example from a real-world system.",
  difficulty: "Intermediate" as const,
  topic: "Distributed systems",
}

type Mode = "practice" | "interview"
const STORAGE_KEY = "socratic-chat-thread"

export default function ChatPage() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [mode, setMode] = useState<Mode>("practice")
  const [secondsLeft, setSecondsLeft] = useState<number>(45 * 60)
  const [timerRunning, setTimerRunning] = useState(false)

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

  useEffect(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as Message[]
        const revived = parsed.map((m) => ({ ...m, timestamp: new Date(m.timestamp) }))
        if (revived.length) setMessages(revived)
      }
    } catch {
      // ignore broken state
    }
  }, [])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages))
  }, [messages])

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
      nextDifficulty: understanding > 0.7 ? "advanced" : "intermediate",
      socraticMoves: moves,
      graphHints,
    }
  }

  const handleSend = async () => {
    if (!input.trim()) return
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
    await new Promise((resolve) => setTimeout(resolve, 350))

    const analysis = evaluateAnswer(content)
    const assistantMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "Давай продолжим диалог и углубим мысль.",
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
          moves: analysis.socraticMoves,
          nextStep:
            analysis.nextDifficulty === "advanced"
              ? "Переходим к PACELC и latency trade-offs."
              : "Сначала проговорим базовое определение partition и trade-off.",
        },
        graph: {
          hints: analysis.graphHints,
        },
      },
    }

    setMessages((prev) => [...prev, assistantMessage])
    setLoading(false)
  }

  const handleRegenerate = async (messageId: string) => {
    const targetIndex = messages.findIndex((msg) => msg.id === messageId)
    if (targetIndex === -1) return

    const previousUser = [...messages]
      .slice(0, targetIndex)
      .reverse()
      .find((msg) => msg.role === "user")

    if (!previousUser) return

    setLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 350))

    const analysis = evaluateAnswer(previousUser.content)
    const regeneratedMessage: Message = {
      id: crypto.randomUUID(),
      role: "assistant",
      content: "Обновил анализ ответа. Посмотрите актуальные рекомендации.",
      timestamp: new Date(),
      metadata: { analysis },
    }

    setMessages((prev) => {
      const idx = prev.findIndex((msg) => msg.id === messageId)
      if (idx === -1) return prev
      const clone = [...prev]
      clone.splice(idx, 1, regeneratedMessage)
      return clone
    })

    setLoading(false)
  }

  return (
    <div className="chat-main">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border/70 bg-card/70 px-4 py-3">
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <span className="uppercase tracking-[0.18em] text-[11px]">Тема</span>
            <span className="font-semibold text-foreground">{QUESTION.topic}</span>
            <span className="px-2 py-1 text-[11px] rounded-full border border-border/60">
              {QUESTION.difficulty}
            </span>
          </div>
          <div className="flex items-center gap-2 text-sm">
            <button
              className={`px-3 py-1 text-[12px] rounded-full border ${mode === "practice" ? "border-primary text-primary" : "border-border/60 text-muted-foreground"}`}
              onClick={() => {
                setMode("practice")
                setTimerRunning(false)
              }}
            >
              Practice
            </button>
            <button
              className={`px-3 py-1 text-[12px] rounded-full border ${mode === "interview" ? "border-primary text-primary" : "border-border/60 text-muted-foreground"}`}
              onClick={() => setMode("interview")}
            >
              Interview Sim
            </button>
            {mode === "interview" ? (
              <div className="ml-3 flex items-center gap-2 text-[12px] text-muted-foreground">
                <span>Таймер</span>
                <span className="font-mono text-foreground">
                  {String(Math.floor(secondsLeft / 60)).padStart(2, "0")}:{String(secondsLeft % 60).padStart(2, "0")}
                </span>
                <button
                  className="px-2 py-1 rounded border border-border/60 text-[11px]"
                  onClick={() => setTimerRunning((v) => !v)}
                >
                  {timerRunning ? "Пауза" : "Старт"}
                </button>
              </div>
            ) : null}
          </div>
        </div>
        <MessageList messages={messages} onRegenerateAction={handleRegenerate} className="flex-1 chat-main__list" />
      </div>
      <ChatInput value={input} onChange={setInput} onSend={handleSend} loading={loading} />
    </div>
  )
}






