"use client"

import { useMemo, useState } from "react"

import { AnswerInput } from "@/components/chat/answer-input"
import { AnalysisPanel } from "@/components/chat/analysis-panel"
import { QuestionCard } from "@/components/chat/question-card"
import { SessionHistoryPanel } from "@/components/chat/session-history-panel"
import { TemplateSelectorModal } from "@/components/chat/template-selector-modal"
import {
  Card,
  CardContent,
} from "@/components/ui/card"

const QUESTION = {
  title: "What is partition tolerance in the CAP theorem?",
  prompt:
    "Explain how partition tolerance influences consistency and availability trade-offs. Include one example from a real-world system.",
  difficulty: "Intermediate" as const,
  topic: "Distributed systems",
}

export default function ChatPage() {
  const [answer, setAnswer] = useState("")
  const [loading, setLoading] = useState(false)
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [analysis, setAnalysis] = useState<{
    understanding: number
    gaps: { label: string; done: boolean; hint?: string }[]
    notes?: string
  } | null>(null)

  const gaps = useMemo(
    () => [
      {
        label: "Define what a network partition is",
        done: answer.toLowerCase().includes("partition"),
        hint: "Mention nodes losing connectivity",
      },
      {
        label: "State the CAP trade-off",
        done: answer.toLowerCase().includes("consistency"),
        hint: "Relate consistency vs availability",
      },
      {
        label: "Add a real-world example",
        done: answer.toLowerCase().includes("example"),
        hint: "E.g. Dynamo, MongoDB, or Kafka",
      },
    ],
    [answer]
  )

  const handleSubmit = async () => {
    if (!answer.trim()) return
    setLoading(true)
    await new Promise((resolve) => setTimeout(resolve, 350))
    const completed = gaps.filter((gap) => gap.done).length
    setAnalysis({
      understanding: Math.min(1, 0.35 + completed * 0.2 + Math.min(answer.length / 400, 0.25)),
      gaps,
      notes:
        completed === gaps.length
          ? "Great coverage. Try contrasting with PACELC next."
          : "Fill the remaining gaps above to strengthen your answer.",
    })
    setLoading(false)
  }

  const handleNewSession = () => {
    setIsModalOpen(true)
  }

  const handleSelectSession = (sessionId: number) => {
    console.log("Select session:", sessionId)
  }

  const handleTemplateSelect = async (
    template: string,
    topic: string,
    level: string
  ) => {
    console.log("Creating session:", { template, topic, level })
    setIsModalOpen(false)
  }

  return (
    <>
      <TemplateSelectorModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onSelect={handleTemplateSelect}
      />
      
      <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
        <aside className="space-y-4">
          <SessionHistoryPanel
            onNewSession={handleNewSession}
            onSelectSession={handleSelectSession}
          />
        </aside>

      <section className="space-y-4">
        <QuestionCard {...QUESTION} />
        <AnswerInput value={answer} onChange={setAnswer} onSubmit={handleSubmit} loading={loading} />
        {analysis ? (
          <AnalysisPanel
            understanding={analysis.understanding}
            gaps={analysis.gaps}
            notes={analysis.notes}
          />
        ) : (
          <Card className="border-dashed border-border/60 bg-card/30">
            <CardContent className="py-10 text-center text-sm text-muted-foreground">
              Submit an answer to see real-time analysis and gaps.
            </CardContent>
          </Card>
        )}
      </section>
      </div>
    </>
  )
}






