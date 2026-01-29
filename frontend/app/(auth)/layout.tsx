import type { ReactNode } from "react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="mx-auto flex min-h-screen max-w-6xl items-center justify-center px-4 py-12">
        <Card className="w-full max-w-lg border-border/60 bg-card/60 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-lg font-semibold tracking-tight text-muted-foreground">
              Claude Tests · Sign in to continue
            </CardTitle>
          </CardHeader>
          <CardContent>{children}</CardContent>
        </Card>
      </div>
    </div>
  )
}






