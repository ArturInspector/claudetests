"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface GraphNode {
  id: string;
  name: string;
  mastery_level?: number;
  topic?: string;
  times_reviewed?: number;
  description?: string;
}

interface RelatedConcept {
  id: string;
  name: string;
  relationship: string;
}

interface NodeDetailsPanelProps {
  node: GraphNode;
  onClose: () => void;
  onNodeSelect?: (nodeId: string) => void;
}

export function NodeDetailsPanel({ node, onClose, onNodeSelect }: NodeDetailsPanelProps) {
  const [relatedConcepts, setRelatedConcepts] = useState<RelatedConcept[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchRelatedConcepts();
  }, [node.id]);

  const fetchRelatedConcepts = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch("http://localhost:8000/api/v1/graph", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) return;

      const data = await response.json();
      
      // Находим связанные концепты
      const related: RelatedConcept[] = [];
      data.graph.relationships.forEach((rel: any) => {
        if (rel.source === node.id) {
          const target = data.graph.concepts.find((c: any) => c.concept_id === rel.target);
          if (target) {
            related.push({
              id: target.concept_id,
              name: target.name,
              relationship: rel.type || "связан с",
            });
          }
        } else if (rel.target === node.id) {
          const source = data.graph.concepts.find((c: any) => c.concept_id === rel.source);
          if (source) {
            related.push({
              id: source.concept_id,
              name: source.name,
              relationship: `обратная связь: ${rel.type || "связан с"}`,
            });
          }
        }
      });

      setRelatedConcepts(related);
    } catch (err) {
      console.error("Error fetching related concepts:", err);
    } finally {
      setLoading(false);
    }
  };

  const getMasteryColor = (mastery: number) => {
    if (mastery >= 0.7) return "bg-green-500";
    if (mastery >= 0.4) return "bg-yellow-500";
    return "bg-slate-500";
  };

  const getMasteryLabel = (mastery: number) => {
    if (mastery >= 0.7) return "Освоено";
    if (mastery >= 0.4) return "В процессе";
    return "Начальный уровень";
  };

  const mastery = node.mastery_level || 0;

  return (
    <Card className="w-full max-w-md bg-card/95 backdrop-blur-sm border shadow-lg">
      {/* Заголовок */}
      <div className="flex items-start justify-between p-4 border-b">
        <div className="flex-1">
          <h2 className="text-lg font-bold mb-1">{node.name}</h2>
          {node.topic && (
            <Badge variant="outline" className="text-xs">
              {node.topic}
            </Badge>
          )}
        </div>
        <button
          onClick={onClose}
          className="text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Закрыть"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            className="h-5 w-5"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fillRule="evenodd"
              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
              clipRule="evenodd"
            />
          </svg>
        </button>
      </div>

      {/* Основная информация */}
      <div className="p-4 space-y-4">
        {/* Mastery Level */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Уровень освоения</span>
            <span className="text-sm font-semibold">{(mastery * 100).toFixed(0)}%</span>
          </div>
          <div className="w-full bg-secondary rounded-full h-2 overflow-hidden">
            <div
              className={`h-full transition-all ${getMasteryColor(mastery)}`}
              style={{ width: `${mastery * 100}%` }}
            />
          </div>
          <p className="text-xs text-muted-foreground mt-1">
            {getMasteryLabel(mastery)}
          </p>
        </div>

        {/* Статистика */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-secondary/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Повторений</p>
            <p className="text-2xl font-bold">{node.times_reviewed || 0}</p>
          </div>
          <div className="bg-secondary/50 rounded-lg p-3">
            <p className="text-xs text-muted-foreground mb-1">Связей</p>
            <p className="text-2xl font-bold">{relatedConcepts.length}</p>
          </div>
        </div>

        {/* Описание */}
        {node.description && (
          <div>
            <h3 className="text-sm font-semibold mb-2">Описание</h3>
            <p className="text-sm text-muted-foreground">{node.description}</p>
          </div>
        )}

        {/* Связанные концепты */}
        <div>
          <h3 className="text-sm font-semibold mb-2">Связанные концепты</h3>
          {loading ? (
            <div className="flex items-center justify-center py-4">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
            </div>
          ) : relatedConcepts.length > 0 ? (
            <div className="space-y-2">
              {relatedConcepts.map((concept) => (
                <button
                  key={concept.id}
                  onClick={() => onNodeSelect?.(concept.id)}
                  className="w-full text-left p-2 rounded-md hover:bg-secondary/50 transition-colors"
                >
                  <p className="text-sm font-medium">{concept.name}</p>
                  <p className="text-xs text-muted-foreground">{concept.relationship}</p>
                </button>
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Нет связанных концептов</p>
          )}
        </div>

        {/* Действия */}
        <div className="pt-2 space-y-2">
          <Button variant="outline" className="w-full" size="sm">
            Начать практику
          </Button>
          <Button variant="ghost" className="w-full" size="sm">
            История изучения
          </Button>
        </div>
      </div>
    </Card>
  );
}

