export type Session = {
  id: number
  topic: string
  level: string | null
  status: string
  created_at: string
  updated_at: string
}

export type SessionSummary = Session & {
  iteration_count: number
  message_count?: number
}

/** One iteration (legacy: question/answer/feedback from sessions API) */
export type IterationMessage = {
  id: number
  number: number
  question: string
  answer: string
  feedback: string | null
  created_at: string
}

/** One chat message from DB (role, content, analysis_json) — full dialogue with analysis */
export type SessionMessage = {
  id: string
  session_id: number
  role: "user" | "assistant"
  content: string
  analysis_json?: Record<string, unknown> | null
  timestamp: string
}

export type SessionDetail = Session & {
  iterations: IterationMessage[]
  /** Dialogue history with analysis (gaps, socratic moves). Prefer this for restore when present. */
  messages?: SessionMessage[]
}

export type SessionCreatePayload = {
  topic: string
  level?: string | null
}

export type AnswerRequest = {
  question: string
  answer: string
}

export type AnswerResponse = {
  iteration: IterationMessage
  similar_context: string[]
}
