"use client"

import { useEffect, useRef } from "react"

import { ChatMessage } from "@/components/chat/chat-message"
import { cn } from "@/lib/utils"
import type { Message } from "@/types/chat"

type Props = {
  messages: Message[]
  onRegenerateAction?: (id: string) => void
  className?: string
}

export function MessageList({ messages, onRegenerateAction, className }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = containerRef.current
    if (node) {
      node.scrollTo({ top: node.scrollHeight, behavior: "smooth" })
    }
  }, [messages.length])

  return (
    <div ref={containerRef} className={cn("chat-message-list", className)}>
      {messages.map((message) => (
        <ChatMessage
          key={message.id}
          message={message}
          onRegenerateAction={onRegenerateAction}
        />
      ))}
    </div>
  )
}


