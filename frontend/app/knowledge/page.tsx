"use client";

import { GraphViewer } from "@/components/knowledge/graph-viewer";

export default function KnowledgePage() {
  return (
    <div className="h-screen w-full bg-background">
      <div className="container mx-auto h-full py-6">
        <div className="mb-4">
          <h1 className="text-3xl font-bold">Knowledge Graph</h1>
          <p className="text-muted-foreground">
            Визуализация вашей карты знаний
          </p>
        </div>
        <div className="h-[calc(100vh-140px)]">
          <GraphViewer />
        </div>
      </div>
    </div>
  );
}

