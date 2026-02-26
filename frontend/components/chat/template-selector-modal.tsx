"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"

type TemplateType = "interview_prep" | "system_design" | "deep_dive"

type Template = {
  id: TemplateType
  name: string
  description: string
  duration: string
  icon: string
  recommended_for: string
}

const TEMPLATES: Template[] = [
  {
    id: "interview_prep",
    name: "Interview Prep",
    description: "Quick questions focused on weak points. Fast-paced practice for technical interviews.",
    duration: "15-30 min",
    icon: "⚡",
    recommended_for: "Junior-Mid devs preparing for interviews",
  },
  {
    id: "system_design",
    name: "System Design",
    description: "Architectural questions with trade-offs. Design scalable systems step by step.",
    duration: "45-60 min",
    icon: "🏗️",
    recommended_for: "Mid-Senior devs, system design rounds",
  },
  {
    id: "deep_dive",
    name: "Deep Dive",
    description: "Thorough exploration with detailed explanations. Master concepts from first principles.",
    duration: "60+ min",
    icon: "🔬",
    recommended_for: "All levels, deep understanding",
  },
]

type TemplateSelectorModalProps = {
  isOpen: boolean
  onClose: () => void
  onSelect: (template: TemplateType, topic: string, level: string) => void
}

export function TemplateSelectorModal({
  isOpen,
  onClose,
  onSelect,
}: TemplateSelectorModalProps) {
  const [selectedTemplate, setSelectedTemplate] = useState<TemplateType | null>(null)
  const [topic, setTopic] = useState("")
  const [level, setLevel] = useState("intermediate")

  if (!isOpen) return null

  const handleSubmit = () => {
    if (!selectedTemplate || !topic.trim()) return
    onSelect(selectedTemplate, topic, level)
    setSelectedTemplate(null)
    setTopic("")
    setLevel("intermediate")
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto mx-4">
        <Card className="border-border/60 bg-card">
          <CardHeader>
            <CardTitle className="text-xl">Create New Session</CardTitle>
            <CardDescription>
              Choose a learning template and topic to get started
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-3">
              <label className="text-sm font-medium">Select Template</label>
              <div className="grid gap-3 md:grid-cols-3">
                {TEMPLATES.map((template) => (
                  <button
                    key={template.id}
                    onClick={() => setSelectedTemplate(template.id)}
                    className={`text-left rounded-lg border p-4 transition-all ${
                      selectedTemplate === template.id
                        ? "border-primary bg-primary/10 ring-2 ring-primary"
                        : "border-border/60 bg-background/30 hover:bg-background/50"
                    }`}
                  >
                    <div className="text-2xl mb-2">{template.icon}</div>
                    <div className="text-sm font-semibold mb-1">{template.name}</div>
                    <div className="text-xs text-muted-foreground mb-2">
                      {template.duration}
                    </div>
                    <div className="text-xs text-muted-foreground leading-relaxed">
                      {template.description}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            {selectedTemplate && (
              <>
                <div className="space-y-2">
                  <label htmlFor="topic" className="text-sm font-medium">
                    Topic
                  </label>
                  <Input
                    id="topic"
                    placeholder="e.g., CAP Theorem, React Hooks, System Design..."
                    value={topic}
                    onChange={(e) => setTopic(e.target.value)}
                    className="bg-background/50"
                  />
                </div>

                <div className="space-y-2">
                  <label className="text-sm font-medium">Your Level</label>
                  <div className="flex gap-2">
                    {["beginner", "intermediate", "advanced"].map((lvl) => (
                      <Button
                        key={lvl}
                        variant={level === lvl ? "default" : "outline"}
                        size="sm"
                        onClick={() => setLevel(lvl)}
                      >
                        {lvl.charAt(0).toUpperCase() + lvl.slice(1)}
                      </Button>
                    ))}
                  </div>
                </div>

                <div className="rounded-lg border border-border/60 bg-background/30 p-3">
                  <div className="text-xs font-medium mb-1">
                    {TEMPLATES.find((t) => t.id === selectedTemplate)?.name}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {TEMPLATES.find((t) => t.id === selectedTemplate)?.recommended_for}
                  </div>
                </div>
              </>
            )}

            <div className="flex gap-3 pt-4">
              <Button variant="outline" onClick={onClose} className="flex-1">
                Cancel
              </Button>
              <Button
                onClick={handleSubmit}
                disabled={!selectedTemplate || !topic.trim()}
                className="flex-1"
              >
                Start Session
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}






