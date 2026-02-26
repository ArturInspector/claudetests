export type MessageRole = "system" | "user" | "assistant"

export type Gap = {
  label: string
  done: boolean
  hint?: string
  importance?: "критично" | "важно" | "желательно"
  why?: string
}

export type Misconception = {
  label: string
  evidence?: string
  correction?: string
}

export type KnowledgeHint = {
  concept: string
  status: "weak" | "unexplored" | "solid"
  action?: string
}

export type SocraticMoveType = "probe" | "challenge" | "extend" | "simplify" | "celebrate"

export type SocraticMove = {
  type: SocraticMoveType
  text: string
  rationale?: string
  target?: string
  difficulty?: "beginner" | "intermediate" | "advanced"
}

export type AnalysisMeta = {
  understanding: number
  confidence?: number
  gaps?: Gap[]
  notes?: string
  misconceptions?: Misconception[]
  nextDifficulty?: "beginner" | "intermediate" | "advanced"
}

export type QuestionMeta = {
  title: string
  difficulty: "Beginner" | "Intermediate" | "Advanced"
  topic?: string
  prompt?: string
}

export type SocraticMeta = {
  moves: SocraticMove[]
  nextStep?: string
  selected_question?: string | null
  selection_rationale?: string | null
}

export type GraphMeta = {
  hints?: KnowledgeHint[]
}

export type MessageMetadata = {
  question?: QuestionMeta
  analysis?: AnalysisMeta
  socratic?: SocraticMeta
  graph?: GraphMeta
}

export type Message = {
  id: string
  role: MessageRole
  content: string
  timestamp: Date
  metadata?: MessageMetadata
}



