"use client"

import { useMemo, useState } from "react"

import { AnswerInput } from "@/components/chat/answer-input"
import { AnalysisPanel } from "@/components/chat/analysis-panel"
import { QuestionCard } from "@/components/chat/question-card"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
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

  return (
    <div className="grid gap-6 lg:grid-cols-[280px_1fr]">
      <aside className="space-y-4">
        <Card className="border-border/60 bg-card/60">
          <CardHeader>
            <CardTitle className="text-sm font-semibold uppercase tracking-[0.18em] text-muted-foreground">
              Sessions
            </CardTitle>
            <CardDescription className="text-xs">
              Quick access to your latest practice sets.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-2">
            <Button variant="secondary" className="w-full">
              + New session
            </Button>
            <div className="rounded-lg border border-border/60 bg-background/30 p-3 text-xs text-muted-foreground">
              Session management is coming next. For now, keep practicing in this draft workspace.
            </div>
          </CardContent>
        </Card>
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
  )
}

