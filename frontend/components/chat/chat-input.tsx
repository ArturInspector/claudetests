"use client"

import { useCallback, type KeyboardEvent } from "react"

import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { cn } from "@/lib/utils"

type Props = {
  value: string
  onChange: (value: string) => void
  onSend: () => void
  loading?: boolean
  className?: string
}

export function ChatInput({ value, onChange, onSend, loading, className }: Props) {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent<HTMLTextAreaElement>) => {
      const isSubmit = (event.metaKey || event.ctrlKey) && event.key === "Enter"
      if (isSubmit) {
        event.preventDefault()
        onSend()
      }
    },
    [onSend]
  )

  return (
    <div className={cn("chat-input", className)}>
      <div className="chat-input__shell">
        <div className="chat-input__hint">
          <span>Введите ответ</span>
          <span>Cmd/Ctrl + Enter</span>
        </div>

        <div className="chat-input__body">
          <Textarea
            value={value}
            onChange={(event) => onChange(event.target.value)}
            onKeyDown={handleKeyDown}
            rows={4}
            placeholder="Опишите свой ответ здесь..."
            disabled={loading}
            className="resize-none bg-transparent"
          />

          <div className="chat-input__actions">
            <Button onClick={onSend} disabled={loading || !value.trim()}>
              {loading ? "Анализ..." : "Отправить →"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}


