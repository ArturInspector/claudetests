import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

type Props = {
  title: string
  prompt: string
  difficulty: "Beginner" | "Intermediate" | "Advanced"
  topic?: string
}

export function QuestionCard({ title, prompt, difficulty, topic }: Props) {
  return (
    <Card className="border-border/60 bg-card/60">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="text-lg font-semibold text-foreground">{title}</CardTitle>
          {topic ? (
            <CardDescription className="mt-1 text-xs uppercase tracking-[0.2em] text-muted-foreground">
              {topic}
            </CardDescription>
          ) : null}
        </div>
        <Badge variant="outline" className="border-primary/40 bg-primary/10 text-primary">
          {difficulty}
        </Badge>
      </CardHeader>
      <CardContent className="space-y-2 text-sm leading-relaxed text-muted-foreground">
        <p>{prompt}</p>
      </CardContent>
    </Card>
  )
}

