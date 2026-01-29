"use client"

import { type KeyboardEvent, useCallback } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"

type Props = {
  value: string
  onChange: (value: string) => void
  onSubmit: () => void
  loading?: boolean
}

export function AnswerInput({ value, onChange, onSubmit, loading }: Props) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      const isSubmit = (event.metaKey || event.ctrlKey) && event.key === "Enter"
      if (isSubmit) {
        event.preventDefault()
        onSubmit()
      }
    },
    [onSubmit]
  )

  return (
    <div className="space-y-2 rounded-2xl border border-border/60 bg-card/60 p-4 shadow-sm">
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>Answer in your own words</span>
        <span>Cmd/Ctrl + Enter to submit</span>
      </div>

      <Textarea
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={handleKeyDown}
        rows={6}
        placeholder="Type your answer here..."
        disabled={loading}
      />

      <div className="flex justify-end">
        <Button onClick={onSubmit} disabled={loading || !value.trim()}>
          {loading ? "Analyzing..." : "Submit →"}
        </Button>
      </div>
    </div>
  )
}

