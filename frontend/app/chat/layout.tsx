import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"

export default function ChatLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gradient-to-b from-background via-[#0c0c10] to-[#0a0a0a] text-foreground">
      <header className="border-b border-border/60 bg-background/40 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-2 text-sm font-semibold uppercase tracking-[0.2em] text-muted-foreground">
            <span className="size-2 rounded-full bg-primary shadow-[0_0_12px] shadow-primary/60" />
            Claude Tests
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm">
              Export
            </Button>
            <Button variant="ghost" size="sm">
              User
            </Button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">{children}</main>
    </div>
  )
}






