"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Card } from "@/components/ui/card";

// Динамический импорт для избежания SSR проблем с Three.js
const ForceGraph3D = dynamic(() => import("react-force-graph-3d"), {
  ssr: false,
});

interface GraphNode {
  id: string;
  name: string;
  mastery_level?: number;
  topic?: string;
  times_reviewed?: number;
}

interface GraphLink {
  source: string;
  target: string;
  type?: string;
}

interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export function GraphViewer() {
  const [graphData, setGraphData] = useState<GraphData>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const fgRef = useRef<any>();

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      
      if (!token) {
        setError("Не авторизован");
        setLoading(false);
        return;
      }

      const response = await fetch("http://localhost:8000/api/v1/graph", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch graph");
      }

      const data = await response.json();
      
      // Преобразуем данные из Neo4j в формат для react-force-graph
      const nodes: GraphNode[] = data.graph.concepts.map((concept: any) => ({
        id: concept.concept_id || concept.name,
        name: concept.name,
        mastery_level: concept.mastery_level || 0,
        topic: concept.topic,
        times_reviewed: concept.times_reviewed || 0,
      }));

      const links: GraphLink[] = data.graph.relationships.map((rel: any) => ({
        source: rel.start_node_id || rel.source,
        target: rel.end_node_id || rel.target,
        type: rel.type || "RELATES_TO",
      }));

      setGraphData({ nodes, links });
      setError(null);
    } catch (err) {
      console.error("Error fetching graph:", err);
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  // Цвет узла на основе mastery level
  const getNodeColor = (node: GraphNode) => {
    const mastery = node.mastery_level || 0;
    
    if (mastery >= 0.7) return "#22c55e"; // Зелёный - освоено
    if (mastery >= 0.4) return "#eab308"; // Жёлтый - частично
    return "#94a3b8"; // Серый - не освоено
  };

  // Размер узла на основе times_reviewed
  const getNodeSize = (node: GraphNode) => {
    const reviews = node.times_reviewed || 0;
    return Math.max(4, Math.min(12, 4 + reviews * 1.5));
  };

  if (loading) {
    return (
      <Card className="h-full flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4" />
          <p className="text-muted-foreground">Загрузка графа знаний...</p>
        </div>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="h-full flex items-center justify-center">
        <div className="text-center text-destructive">
          <p className="font-semibold mb-2">Ошибка загрузки</p>
          <p className="text-sm">{error}</p>
        </div>
      </Card>
    );
  }

  if (graphData.nodes.length === 0) {
    return (
      <Card className="h-full flex items-center justify-center">
        <div className="text-center text-muted-foreground">
          <p className="font-semibold mb-2">Граф знаний пуст</p>
          <p className="text-sm">Начните сессию чтобы построить карту знаний</p>
        </div>
      </Card>
    );
  }

  return (
    <Card className="h-full relative overflow-hidden">
      <ForceGraph3D
        ref={fgRef}
        graphData={graphData}
        nodeLabel={(node: any) => `${node.name} (mastery: ${(node.mastery_level * 100).toFixed(0)}%)`}
        nodeColor={getNodeColor}
        nodeVal={getNodeSize}
        linkDirectionalParticles={2}
        linkDirectionalParticleSpeed={0.005}
        backgroundColor="#0a0a0a"
        showNavInfo={false}
      />
      
      {/* Легенда */}
      <div className="absolute top-4 right-4 bg-card/90 backdrop-blur-sm border rounded-lg p-4 space-y-2">
        <p className="text-sm font-semibold mb-2">Легенда</p>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-3 h-3 rounded-full bg-[#22c55e]" />
          <span>Освоено (≥70%)</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-3 h-3 rounded-full bg-[#eab308]" />
          <span>Частично (40-70%)</span>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <div className="w-3 h-3 rounded-full bg-[#94a3b8]" />
          <span>Не освоено (&lt;40%)</span>
        </div>
      </div>

      {/* Статистика */}
      <div className="absolute bottom-4 left-4 bg-card/90 backdrop-blur-sm border rounded-lg p-4">
        <p className="text-sm font-semibold mb-2">Статистика</p>
        <div className="space-y-1 text-xs">
          <p>Концептов: {graphData.nodes.length}</p>
          <p>Связей: {graphData.links.length}</p>
        </div>
      </div>
    </Card>
  );
}

