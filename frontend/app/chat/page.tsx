"use client"

import { useMemo, useState } from "react"

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

export default function ChatPage() {
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)

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

  const evaluateAnswer = (answer: string) => {
    const normalized = answer.toLowerCase()
    const hasPartition = normalized.includes("partition")
    const hasTradeoff = normalized.includes("trade-off") || normalized.includes("tradeoff") || normalized.includes("однако")
    const hasExample = normalized.includes("например") || normalized.includes("e.g.") || normalized.includes("dynamo") || normalized.includes("mongo")
    const hasNumbers = /\d+/.test(answer)
    const lengthScore = Math.min(1, answer.length / 500)

    const gaps: Gap[] = []
    if (!hasPartition) gaps.push({ label: "Опиши, что такое сетевой partition", done: false, hint: "Разрыв связности между нодами" })
    if (!hasTradeoff) gaps.push({ label: "Отрази CAP trade-off", done: false, hint: "Связь consistency vs availability" })
    if (!hasExample) gaps.push({ label: "Приведи реальный пример", done: false, hint: "Dynamo, MongoDB, Kafka" })

    const base = 0.3 + lengthScore * 0.3 + (hasTradeoff ? 0.2 : 0) + (hasExample ? 0.1 : 0) + (hasNumbers ? 0.1 : 0)
    const understanding = Math.min(1, base)
    const confidence = Math.min(1, 0.25 + lengthScore * 0.5 + (hasNumbers ? 0.1 : 0))

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

    const misconceptions = !hasPartition
      ? [{ label: "CAP без partition — неполное определение", correction: "Partition tolerance обязательна" }]
      : []

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
      <MessageList messages={messages} onRegenerateAction={handleRegenerate} className="flex-1 chat-main__list" />
      <ChatInput value={input} onChange={setInput} onSend={handleSend} loading={loading} />
    </div>
  )
}






