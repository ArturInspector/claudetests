import type { ReactNode } from "react"
import Link from "next/link"

export default function AuthLayout({ children }: { children: ReactNode }) {
  return (
    <div className="relative min-h-screen flex items-center justify-center bg-[#050505] overflow-hidden text-white selection:bg-orange-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-0 left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-blue-900/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[500px] w-[500px] rounded-full bg-orange-900/10 blur-[100px]" />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03]" />
      </div>

      <div className="relative z-10 w-full max-w-md px-6">
        <div className="mb-8 text-center">
          <Link href="/" className="inline-flex items-center gap-3 group">
            <div className="size-2 rounded-full bg-orange-500 shadow-[0_0_12px_currentColor] transition-transform group-hover:scale-110" />
            <span className="text-sm font-bold uppercase tracking-[0.2em] text-white/70 transition-colors group-hover:text-white">
              Claude Tests
            </span>
          </Link>
        </div>

        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 backdrop-blur-xl shadow-2xl shadow-black/50">
           {children}
        </div>
        
        <div className="mt-8 text-center text-[10px] text-white/20 uppercase tracking-widest">
          Secure Cognitive Environment
        </div>
      </div>
    </div>
  )
}
