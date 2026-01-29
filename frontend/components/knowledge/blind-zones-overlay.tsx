"use client";

import { useEffect, useState } from "react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface BlindZone {
  name: string;
  mastery: number;
  type: "weak" | "unexplored" | "forgotten";
}

interface BlindZonesOverlayProps {
  isVisible: boolean;
  onClose: () => void;
  onFocusNode?: (nodeName: string) => void;
}

export function BlindZonesOverlay({ isVisible, onClose, onFocusNode }: BlindZonesOverlayProps) {
  const [blindZones, setBlindZones] = useState<BlindZone[]>([]);
  const [recommendations, setRecommendations] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (isVisible) {
      fetchBlindZones();
    }
  }, [isVisible]);

  const fetchBlindZones = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      if (!token) return;

      const response = await fetch("http://localhost:8000/api/v1/graph/blind-zones", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) throw new Error("Failed to fetch blind zones");

      const data = await response.json();
      setBlindZones(data.blind_zones || []);
      setRecommendations(data.recommendations || []);
    } catch (err) {
      console.error("Error fetching blind zones:", err);
    } finally {
      setLoading(false);
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "weak":
        return "Слабое понимание";
      case "unexplored":
        return "Не изучено";
      case "forgotten":
        return "Забыто";
      default:
        return "Неизвестно";
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case "weak":
        return "bg-yellow-500/20 text-yellow-700 border-yellow-500/50";
      case "unexplored":
        return "bg-slate-500/20 text-slate-700 border-slate-500/50";
      case "forgotten":
        return "bg-red-500/20 text-red-700 border-red-500/50";
      default:
        return "bg-secondary";
    }
  };

  const getTypeIcon = (type: string) => {
    switch (type) {
      case "weak":
        return "⚠️";
      case "unexplored":
        return "🔍";
      case "forgotten":
        return "💤";
      default:
        return "❓";
    }
  };

  if (!isVisible) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        {/* Заголовок */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold">Blind Zones</h2>
            <p className="text-sm text-muted-foreground mt-1">
              Области требующие внимания
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Закрыть"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-6 w-6"
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

        {/* Контент */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
            </div>
          ) : (
            <>
              {/* Рекомендации */}
              {recommendations.length > 0 && (
                <div className="bg-primary/10 border border-primary/20 rounded-lg p-4">
                  <h3 className="font-semibold mb-3 flex items-center gap-2">
                    💡 Рекомендации
                  </h3>
                  <ul className="space-y-2">
                    {recommendations.map((rec, idx) => (
                      <li key={idx} className="text-sm flex items-start gap-2">
                        <span className="text-primary mt-0.5">•</span>
                        <span>{rec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Список blind zones */}
              {blindZones.length > 0 ? (
                <div>
                  <h3 className="font-semibold mb-4">
                    Обнаружено проблем: {blindZones.length}
                  </h3>
                  <div className="space-y-3">
                    {blindZones.map((zone, idx) => (
                      <div
                        key={idx}
                        className={`border rounded-lg p-4 transition-all hover:shadow-md ${getTypeColor(
                          zone.type
                        )}`}
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-xl">{getTypeIcon(zone.type)}</span>
                              <h4 className="font-semibold">{zone.name}</h4>
                            </div>
                            <div className="flex items-center gap-3">
                              <Badge variant="outline" className="text-xs">
                                {getTypeLabel(zone.type)}
                              </Badge>
                              {zone.mastery > 0 && (
                                <span className="text-xs text-muted-foreground">
                                  Mastery: {(zone.mastery * 100).toFixed(0)}%
                                </span>
                              )}
                            </div>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onFocusNode?.(zone.name)}
                            className="ml-2"
                          >
                            Показать
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎉</div>
                  <h3 className="text-xl font-semibold mb-2">Отличная работа!</h3>
                  <p className="text-muted-foreground">
                    Blind zones не обнаружены. Продолжайте в том же духе!
                  </p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Футер */}
        <div className="border-t p-4 bg-secondary/20">
          <div className="flex items-center justify-between text-xs text-muted-foreground">
            <span>Обновляется после каждой сессии</span>
            <Button variant="outline" size="sm" onClick={fetchBlindZones}>
              Обновить
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

