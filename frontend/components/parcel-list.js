"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { fetchParcels, getCropImageUrl } from "@/lib/api-client";

export default function ParcelList({ condition, refreshTrigger }) {
  const [parcels, setParcels] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const isDamaged = condition === "damaged";
  const title = isDamaged ? "Damaged Parcels" : "Undamaged Parcels";
  const icon = isDamaged ? "⚠️" : "✅";
  const gradient = isDamaged
    ? "from-red-500/10 to-orange-500/5"
    : "from-emerald-500/10 to-green-500/5";
  const borderColor = isDamaged
    ? "border-red-500/20"
    : "border-emerald-500/20";

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      try {
        const data = await fetchParcels({ condition, limit: 50 });
        if (!cancelled) {
          setParcels(data.parcels);
          setTotal(data.total);
        }
      } catch (err) {
        console.error(`Failed to load ${condition} parcels:`, err);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => { cancelled = true; };
  }, [condition, refreshTrigger]);

  return (
    <Card
      id={`parcel-list-${condition}`}
      className={`bg-gradient-to-br ${gradient} ${borderColor} border`}
    >
      <CardHeader>
        <CardTitle className="text-lg flex items-center justify-between">
          <span className="flex items-center gap-2">
            <span className="text-xl">{icon}</span>
            {title}
          </span>
          <Badge variant="secondary" className="text-xs">
            {total} total
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <svg className="animate-spin h-6 w-6 text-muted-foreground" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          </div>
        ) : parcels.length === 0 ? (
          <p className="text-center text-muted-foreground py-8 text-sm">
            No {condition} parcels detected yet.
          </p>
        ) : (
          <div className="max-h-[400px] overflow-y-auto rounded-md">
            <Table>
              <TableHeader>
                <TableRow className="hover:bg-transparent">
                  <TableHead className="w-[60px]">ID</TableHead>
                  <TableHead>Track</TableHead>
                  <TableHead>Confidence</TableHead>
                  <TableHead>Action</TableHead>
                  <TableHead className="text-right">Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {parcels.map((parcel) => (
                  <TableRow
                    key={parcel.id}
                    id={`parcel-row-${parcel.id}`}
                    onClick={() => router.push(`/parcels/${parcel.id}`)}
                    className="cursor-pointer transition-colors duration-200 hover:bg-accent/50"
                  >
                    <TableCell className="font-mono text-xs">
                      #{parcel.id}
                    </TableCell>
                    <TableCell>
                      <span className="font-mono text-xs bg-muted px-2 py-0.5 rounded">
                        T-{parcel.track_id}
                      </span>
                    </TableCell>
                    <TableCell>
                      <span className={`font-semibold ${
                        parcel.confidence_score >= 0.8
                          ? "text-emerald-400"
                          : parcel.confidence_score >= 0.6
                            ? "text-yellow-400"
                            : "text-red-400"
                      }`}>
                        {(parcel.confidence_score * 100).toFixed(1)}%
                      </span>
                    </TableCell>
                    <TableCell>
                      <Badge
                        variant={parcel.action === "inspection" ? "destructive" : "secondary"}
                        className="text-xs"
                      >
                        {parcel.action === "inspection" ? "🔍 Inspection" : "📤 Normal"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right text-xs text-muted-foreground">
                      {new Date(parcel.detected_at).toLocaleTimeString()}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
