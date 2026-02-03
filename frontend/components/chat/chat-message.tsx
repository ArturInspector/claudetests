"use client"

import type { Message } from "@/types/chat"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"

type Props = {
  message: Message
  onRegenerateAction?: (id: string) => void
}

const difficultyTone: Record<string, string> = {
  Beginner: "badge-beginner",
  Intermediate: "badge-intermediate",
  Advanced: "badge-advanced",
}

const roleTitle: Record<Message["role"], string> = {
  system: "System",
  user: "You",
  assistant: "Assistant",
}

const moveLabels = {
  probe: "Наводящий вопрос",
  challenge: "Challenge",
  extend: "Углубление",
  simplify: "Упростить",
  celebrate: "Подтвердить",
}

export function ChatMessage({ message, onRegenerateAction }: Props) {
  const { role, metadata } = message
  const isUser = role === "user"
  const hasQuestion = Boolean(metadata?.question)
  const hasAnalysis = Boolean(metadata?.analysis)
  const hasSocratic = Boolean(metadata?.socratic?.moves?.length)
  const hasGraphHints = Boolean(metadata?.graph?.hints?.length)
  const understanding = Math.round((metadata?.analysis?.understanding ?? 0) * 100)
  const confidence = Math.round((metadata?.analysis?.confidence ?? 0) * 100)

  return (
    <div className={cn("chat-message", isUser && "user")}>
      <div className="chat-message__container">
        <div className="chat-message__bubble">
          <div className="chat-message__role">
            {roleTitle[role]}
          </div>

          {hasQuestion && metadata?.question ? (
            <Card>
              <CardHeader className="flex flex-row items-center justify-between gap-3 pb-3 !p-0">
                <CardTitle>
                  {metadata.question.title}
                </CardTitle>
                <Badge
                  data-variant="outline"
                  className={cn("text-[11px]", difficultyTone[metadata.question.difficulty])}
                >
                  {metadata.question.difficulty}
                </Badge>
              </CardHeader>
              <CardContent className="space-y-2 pt-0 text-sm text-muted-foreground !p-0">
                {metadata.question.topic ? (
                  <div className="text-[11px] uppercase tracking-[0.24em] text-muted-foreground/80 mt-1">
                    {metadata.question.topic}
                  </div>
                ) : null}
                <p className="leading-relaxed chat-message__text">
                  {metadata.question.prompt ?? message.content}
                </p>
              </CardContent>
            </Card>
          ) : (
            <p className="chat-message__text">{message.content}</p>
          )}

          {hasAnalysis && metadata?.analysis ? (
            <div className="chat-analysis">
              <div className="chat-analysis__header">
                <span>Understanding</span>
                <span className="font-medium">{understanding}%</span>
              </div>
              <div className="chat-analysis__progress">
                <div className="chat-analysis__progress-bar" style={{ width: `${Math.min(100, Math.max(0, understanding))}%` }} />
              </div>

              {metadata.analysis.confidence !== undefined ? (
                <div className="chat-analysis__header !mt-1">
                  <span>Confidence</span>
                  <span className="font-medium">{confidence}%</span>
                </div>
              ) : null}

              {metadata.analysis.gaps && metadata.analysis.gaps.length > 0 ? (
                <div className="chat-analysis__gaps">
                  <div className="text-xs font-semibold uppercase tracking-[0.18em] text-muted-foreground">Gaps</div>
                  {metadata.analysis.gaps.map((gap) => (
                    <div key={gap.label} className={cn("chat-analysis__gap", gap.done && "done")}>
                      <span className={cn("mt-[2px] text-xs", gap.done ? "text-emerald-400" : "text-muted-foreground")}>
                        {gap.done ? "✓" : "•"}
                      </span>
                      <div className="flex-1">
                        <div className="text-foreground/90">{gap.label}</div>
                        {!gap.done && gap.hint ? <div className="hint">{gap.hint}</div> : null}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}

              {metadata.analysis.misconceptions && metadata.analysis.misconceptions.length > 0 ? (
                <div className="chat-analysis__section">
                  <div className="chat-analysis__title">Misconceptions</div>
                  <div className="space-y-2">
                    {metadata.analysis.misconceptions.map((item) => (
                      <div key={item.label} className="chat-analysis__pill">
                        <div className="font-medium">{item.label}</div>
                        {item.evidence ? <div className="text-xs text-muted-foreground">{item.evidence}</div> : null}
                        {item.correction ? <div className="text-xs text-emerald-400">{item.correction}</div> : null}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              {metadata.analysis.nextDifficulty ? (
                <div className="chat-analysis__section">
                  <div className="chat-analysis__title">Next difficulty</div>
                  <Badge variant="outline" className="text-[11px]">
                    {metadata.analysis.nextDifficulty}
                  </Badge>
                </div>
              ) : null}

              {metadata.analysis.notes ? (
                <div className="chat-analysis__notes">
                  {metadata.analysis.notes}
                </div>
              ) : null}

              {onRegenerateAction ? (
                <div className="flex justify-end">
                  <Button variant="ghost" size="sm" className="text-xs" onClick={() => onRegenerateAction(message.id)}>
                    ↻ Regenerate
                  </Button>
                </div>
              ) : null}
            </div>
          ) : null}

          {hasSocratic && metadata?.socratic?.moves ? (
            <div className="chat-analysis chat-analysis--secondary">
              <div className="chat-analysis__title">Socratic moves</div>
              <div className="space-y-2">
                {metadata.socratic.moves.map((move, idx) => (
                  <div key={`${move.type}-${idx}`} className="chat-analysis__pill">
                    <div className="flex items-center gap-2">
                      <Badge variant="outline" className="text-[11px] capitalize">
                        {moveLabels[move.type] ?? move.type}
                      </Badge>
                      {move.difficulty ? (
                        <Badge variant="outline" className="text-[11px]">
                          {move.difficulty}
                        </Badge>
                      ) : null}
                    </div>
                    <div className="text-sm text-foreground leading-relaxed">{move.text}</div>
                    {move.rationale ? <div className="text-xs text-muted-foreground">{move.rationale}</div> : null}
                  </div>
                ))}
              </div>
              {metadata.socratic.nextStep ? (
                <div className="chat-analysis__notes">{metadata.socratic.nextStep}</div>
              ) : null}
            </div>
          ) : null}

          {hasGraphHints && metadata?.graph?.hints ? (
            <div className="chat-analysis chat-analysis--secondary">
              <div className="chat-analysis__title">Knowledge Graph</div>
              <div className="flex flex-wrap gap-2">
                {metadata.graph.hints.map((hint) => (
                  <Badge
                    key={hint.concept}
                    variant="outline"
                    className={cn(
                      "text-[11px]",
                      hint.status === "weak" && "border-amber-500/50 text-amber-300",
                      hint.status === "unexplored" && "border-sky-500/50 text-sky-300",
                      hint.status === "solid" && "border-emerald-500/50 text-emerald-300"
                    )}
                  >
                    {hint.concept}
                    {hint.action ? ` · ${hint.action}` : ""}
                  </Badge>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  )
}


