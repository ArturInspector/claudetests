import type { HTMLAttributes } from "react"

import { cn } from "@/lib/utils"

type Variant = "default" | "primary" | "destructive" | "outline"
type BadgeProps = HTMLAttributes<HTMLDivElement> & { variant?: Variant }

export function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div
      data-slot="badge"
      data-variant={variant}
      className={cn(className)}
      {...props}
    />
  )
}

