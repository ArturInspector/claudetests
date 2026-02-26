"use client";

import { useEffect, useRef, useState } from "react";
import dynamic from "next/dynamic";
import { Button } from "@/components/ui/button";
import { NodeDetailsPanel } from "./node-details-panel";
import { BlindZonesOverlay } from "./blind-zones-overlay";
import { useAuthStore } from "@/stores/auth";
import { Maximize2, ZoomIn } from "lucide-react";

// Dynamic import to avoid SSR issues with Three.js
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
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [showBlindZones, setShowBlindZones] = useState(false);
  const fgRef = useRef<any>();

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    try {
      setLoading(true);
      const token =
        useAuthStore.getState().token ||
        (typeof window !== "undefined" ? localStorage.getItem("access_token") : null) ||
        (typeof document !== "undefined"
          ? document.cookie.match(/(?:^|; )access_token=([^;]+)/)?.[1]
          : null);
      
      if (!token) {
        setError("Authorization required");
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

  const getNodeColor = (node: GraphNode) => {
    const mastery = node.mastery_level || 0;
    
    if (mastery >= 0.7) return "#10b981"; // Emerald/Green (Mastered)
    if (mastery >= 0.4) return "#ff3c00"; // Orange (In Progress)
    return "#3b82f6"; // Blue (New/Unexplored)
  };

  const getNodeSize = (node: GraphNode) => {
    const reviews = node.times_reviewed || 0;
    const baseSize = Math.max(4, Math.min(12, 4 + reviews * 1.5));
    
    if (selectedNode && node.id === selectedNode.id) {
      return baseSize * 1.5;
    }
    
    return baseSize;
  };

  const handleNodeClick = (node: any) => {
    setSelectedNode(node as GraphNode);
    
    if (fgRef.current) {
      const distance = 150;
      const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);
      
      fgRef.current.cameraPosition(
        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio },
        node,
        1500
      );
    }
  };

  const handleNodeHover = (node: any) => {
    setHoveredNode(node as GraphNode | null);
    if (typeof document !== "undefined") {
      document.body.style.cursor = node ? "pointer" : "default";
    }
  };

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto" />
          <p className="text-white/50 text-xs font-bold uppercase tracking-widest">Constructing Neural Map...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-red-400">
          <p className="font-bold uppercase tracking-wider mb-2">Connection Failure</p>
          <p className="text-sm opacity-70">{error}</p>
        </div>
      </div>
    );
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-white/40">
          <p className="font-bold uppercase tracking-wider mb-2">Neural Network Empty</p>
          <p className="text-sm">Initiate sessions to populate cognitive graph.</p>
        </div>
      </div>
    );
  }

  const handleFocusNode = (nodeName: string) => {
    const node = graphData.nodes.find((n) => n.name === nodeName);
    if (node) {
      handleNodeClick(node);
      setShowBlindZones(false);
    }
  };

  return (
    <>
      <div className="h-full relative overflow-hidden">
        {/* Blind Zones Trigger */}
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-10">
          <button
            onClick={() => setShowBlindZones(true)}
            className="group flex items-center gap-2 rounded-full border border-white/10 bg-black/40 px-4 py-2 text-xs font-bold uppercase tracking-wider text-white backdrop-blur-md transition-all hover:bg-white/10 hover:border-orange-500/50"
          >
            <ZoomIn className="size-3 text-orange-500" />
            Scan Blind Zones
          </button>
        </div>

        <ForceGraph3D
          ref={fgRef}
          graphData={graphData}
          nodeLabel={(node: any) => `${node.name} (${(node.mastery_level * 100).toFixed(0)}%)`}
          nodeColor={getNodeColor}
          nodeVal={getNodeSize}
          onNodeClick={handleNodeClick}
          onNodeHover={handleNodeHover}
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.005}
          linkWidth={1}
          linkOpacity={0.3}
          backgroundColor="rgba(0,0,0,0)" // Transparent to show page background
          showNavInfo={false}
          linkColor={() => "#ffffff33"}
        />
      
      {/* Legend */}
      <div className="absolute top-6 right-6 rounded-xl border border-white/5 bg-black/40 p-4 backdrop-blur-md">
        <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-3">Synaptic Strength</p>
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-xs text-white/70">
            <div className="size-2 rounded-full bg-[#10b981] shadow-[0_0_8px_rgba(16,185,129,0.5)]" />
            <span>Mastered (≥70%)</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-white/70">
            <div className="size-2 rounded-full bg-[#ff3c00] shadow-[0_0_8px_rgba(255,60,0,0.5)]" />
            <span>Developing (40-70%)</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-white/70">
            <div className="size-2 rounded-full bg-[#3b82f6] shadow-[0_0_8px_rgba(59,130,246,0.5)]" />
            <span>Unexplored (&lt;40%)</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="absolute bottom-6 left-6 rounded-xl border border-white/5 bg-black/40 p-4 backdrop-blur-md">
        <p className="text-[10px] font-bold uppercase tracking-widest text-white/30 mb-3">Network Metrics</p>
        <div className="space-y-1 text-xs text-white/70 font-mono">
          <p>Nodes: {graphData.nodes.length}</p>
          <p>Links: {graphData.links.length}</p>
        </div>
      </div>

      {/* Selected Node Details */}
      {selectedNode && (
        <div className="absolute top-20 left-6 max-w-sm z-20">
          <NodeDetailsPanel
            node={selectedNode}
            onClose={() => setSelectedNode(null)}
            onNodeSelect={(nodeId) => {
              const node = graphData.nodes.find((n) => n.id === nodeId);
              if (node) {
                handleNodeClick(node);
              }
            }}
          />
        </div>
      )}

      {/* Hover tooltip */}
      {hoveredNode && !selectedNode && (
        <div className="absolute top-24 left-6 pointer-events-none rounded-lg border border-white/10 bg-black/80 px-3 py-2 backdrop-blur-md">
          <p className="font-bold text-sm text-white">{hoveredNode.name}</p>
          <p className="text-[10px] uppercase tracking-wider text-orange-500">
            Click to analyze
          </p>
        </div>
      )}
      </div>

      {/* Blind Zones Overlay */}
      <BlindZonesOverlay
        isVisible={showBlindZones}
        onClose={() => setShowBlindZones(false)}
        onFocusNode={handleFocusNode}
      />
    </>
  );
}
