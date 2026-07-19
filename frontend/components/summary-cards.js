"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { fetchDashboardSummary } from "@/lib/api-client";

export default function SummaryCards({ refreshTrigger }) {
  const [summary, setSummary] = useState({
    total_detected: 0,
    total_damaged: 0,
    total_undamaged: 0,
  });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const data = await fetchDashboardSummary();
        if (!cancelled) setSummary(data);
      } catch (err) {
        console.error("Failed to load summary:", err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [refreshTrigger]);

  const cards = [
    {
      title: "Total Detected",
      value: summary.total_detected,
      icon: "📦",
      gradient: "from-blue-500/20 to-blue-600/10",
      border: "border-blue-500/30",
      text: "text-blue-400",
    },
    {
      title: "Total Damaged",
      value: summary.total_damaged,
      icon: "⚠️",
      gradient: "from-red-500/20 to-red-600/10",
      border: "border-red-500/30",
      text: "text-red-400",
    },
    {
      title: "Total Undamaged",
      value: summary.total_undamaged,
      icon: "✅",
      gradient: "from-emerald-500/20 to-emerald-600/10",
      border: "border-emerald-500/30",
      text: "text-emerald-400",
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {cards.map((card) => (
        <Card
          key={card.title}
          id={`summary-card-${card.title.toLowerCase().replace(/\s+/g, "-")}`}
          className={`bg-gradient-to-br ${card.gradient} ${card.border} border backdrop-blur-sm transition-all duration-300 hover:scale-[1.02] hover:shadow-lg`}
        >
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {card.title}
            </CardTitle>
            <span className="text-2xl">{card.icon}</span>
          </CardHeader>
          <CardContent>
            <div className={`text-4xl font-bold ${card.text}`}>
              {loading ? (
                <span className="animate-pulse">—</span>
              ) : (
                card.value
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
