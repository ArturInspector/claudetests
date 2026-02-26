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
}

export type Message = {
  id: number
  number: number
  question: string
  answer: string
  feedback: string | null
  created_at: string
}

export type SessionDetail = Session & {
  iterations: Message[]
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
  iteration: Message
  similar_context: string[]
}
