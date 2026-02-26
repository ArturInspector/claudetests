import * as React from "react"
import { cn } from "@/lib/utils"

type Variant = "default" | "secondary" | "ghost" | "outline" | "destructive"
type Size = "default" | "sm" | "lg" | "icon"

function Button({
  className,
  variant = "default",
  size = "default",
  ...props
}: React.ComponentProps<"button"> & {
  variant?: Variant
  size?: Size
}) {
  return (
    <button
      data-slot="button"
      data-variant={variant}
      data-size={size}
      className={cn(className)}
      {...props}
    />
  )
}

export { Button }
