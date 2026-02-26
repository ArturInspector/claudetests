"use client";

import { GraphViewer } from "@/components/knowledge/graph-viewer";
import Link from "next/link";
import { ChevronLeft, Share2 } from "lucide-react";

export default function KnowledgePage() {
  return (
    <div className="relative h-screen w-full bg-[#050505] text-white overflow-hidden selection:bg-orange-500/30">
      {/* Background Ambience */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-0 left-1/2 h-[600px] w-[600px] -translate-x-1/2 rounded-full bg-blue-900/10 blur-[120px]" />
        <div className="absolute bottom-0 right-0 h-[500px] w-[500px] rounded-full bg-orange-900/10 blur-[100px]" />
        <div className="absolute inset-0 bg-[url('/noise.png')] opacity-[0.03]" />
      </div>

      <div className="relative z-10 flex h-full flex-col">
        {/* Header */}
        <header className="border-b border-white/5 bg-[#050505]/80 backdrop-blur-md px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-4">
             <Link href="/chat" className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-white/50 hover:text-white transition-colors">
               <ChevronLeft className="size-4" />
               Return to Console
             </Link>
             <div className="h-4 w-px bg-white/10" />
             <div className="flex items-center gap-2">
               <div className="size-1.5 animate-pulse rounded-full bg-blue-500 shadow-[0_0_8px_currentColor]" />
               <span className="text-sm font-bold uppercase tracking-[0.2em] text-white">
                 Neural Map
               </span>
             </div>
          </div>
          
          <button className="flex items-center gap-2 text-xs font-medium text-white/50 hover:text-white transition-colors">
            <Share2 className="size-3" />
            Share Graph
          </button>
        </header>

        {/* Content */}
        <div className="flex-1 relative">
           <div className="absolute top-6 left-6 z-20 max-w-sm pointer-events-none">
             <h1 className="text-2xl font-bold text-white mb-1">Knowledge Graph</h1>
             <p className="text-xs text-white/40 leading-relaxed">
               Visual representation of your cognitive structure. 
               Nodes represent concepts; edges represent relationships.
             </p>
           </div>
           
           <div className="h-full w-full border-t border-white/5 bg-black/20 backdrop-blur-sm">
             <GraphViewer />
           </div>
        </div>
      </div>
    </div>
  );
}
