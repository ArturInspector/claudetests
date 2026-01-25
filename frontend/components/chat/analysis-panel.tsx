import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

type Gap = {
  label: string
  done: boolean
  hint?: string
}

type Props = {
  understanding: number
  gaps: Gap[]
  notes?: string
}

export function AnalysisPanel({ understanding, gaps, notes }: Props) {
  return (
    <Card className="border-border/60 bg-card/60">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Analysis</CardTitle>
        <Badge variant="primary">{Math.round(understanding * 100)}% understood</Badge>
      </CardHeader>
      <CardContent className="space-y-4 text-sm text-muted-foreground">
        <div className="space-y-2">
          <p className="text-xs uppercase tracking-[0.18em] text-muted-foreground/80">
            Gaps
          </p>
          <ul className="space-y-2">
            {gaps.map((gap) => (
              <li
                key={gap.label}
                className="flex items-start gap-3 rounded-lg bg-background/30 px-3 py-2"
              >
                <span
                  className="mt-0.5 inline-block size-2 rounded-full"
                  style={{ backgroundColor: gap.done ? "#22c55e" : "#eab308" }}
                />
                <div className="space-y-1">
                  <p className="font-medium text-foreground">{gap.label}</p>
                  {gap.hint ? <p className="text-xs">{gap.hint}</p> : null}
                </div>
              </li>
            ))}
          </ul>
        </div>

        {notes ? (
          <div className="rounded-lg border border-border/60 bg-background/30 px-3 py-2 text-xs leading-relaxed">
            {notes}
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}

