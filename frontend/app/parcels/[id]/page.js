"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchParcelDetail, getCropImageUrl } from "@/lib/api-client";

export default function ParcelDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [parcel, setParcel] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    async function load() {
      try {
        const data = await fetchParcelDetail(params.id);
        setParcel(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [params.id]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
        <svg className="animate-spin h-8 w-8 text-purple-400" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      </div>
    );
  }

  if (error || !parcel) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
        <Card className="max-w-md w-full">
          <CardContent className="pt-6 text-center">
            <p className="text-red-400 mb-4">❌ {error || "Parcel not found"}</p>
            <Button variant="outline" onClick={() => router.push("/")}>
              ← Back to Dashboard
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  const isDamaged = parcel.condition === "damaged";
  const cropUrl = getCropImageUrl(parcel.image_path);

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Background decoration */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/60 border-b border-border/40">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-2xl">📦</span>
            <h1 className="text-lg font-bold text-foreground">
              Parcel #{parcel.id}
            </h1>
          </div>
          <Button
            id="back-button"
            variant="ghost"
            size="icon"
            onClick={() => router.push("/")}
            className="hover:bg-destructive/10 hover:text-red-400 transition-all duration-300"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Crop Image */}
          <Card
            id="parcel-image-card"
            className={`border ${isDamaged ? "border-red-500/30" : "border-emerald-500/30"} overflow-hidden`}
          >
            <CardContent className="p-0">
              {cropUrl ? (
                <img
                  src={cropUrl}
                  alt={`Parcel #${parcel.id} crop`}
                  className="w-full h-auto object-contain bg-black/50 min-h-[250px]"
                  onError={(e) => {
                    e.target.src = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMDAiIGhlaWdodD0iMjUwIiB2aWV3Qm94PSIwIDAgMzAwIDI1MCIgZmlsbD0ibm9uZSI+PHJlY3Qgd2lkdGg9IjMwMCIgaGVpZ2h0PSIyNTAiIGZpbGw9IiMxYTFhMmUiLz48dGV4dCB4PSI1MCUiIHk9IjUwJSIgZG9taW5hbnQtYmFzZWxpbmU9Im1pZGRsZSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzZiNzI4MCIgZm9udC1zaXplPSIxNiI+Tm8gaW1hZ2UgYXZhaWxhYmxlPC90ZXh0Pjwvc3ZnPg==";
                  }}
                />
              ) : (
                <div className="flex items-center justify-center h-[250px] bg-muted/20 text-muted-foreground">
                  No image available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Details */}
          <Card id="parcel-details-card" className="border-muted/30">
            <CardHeader>
              <CardTitle className="text-xl flex items-center gap-2">
                <span>{isDamaged ? "⚠️" : "✅"}</span>
                Parcel Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-5">
              {/* Condition */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Condition</span>
                <Badge
                  className={`text-sm px-3 py-1 ${
                    isDamaged
                      ? "bg-red-500/20 text-red-400 border border-red-500/40"
                      : "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                  }`}
                >
                  {parcel.condition.toUpperCase()}
                </Badge>
              </div>

              {/* Confidence */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Confidence Score</span>
                <span className={`font-bold text-lg ${
                  parcel.confidence_score >= 0.8
                    ? "text-emerald-400"
                    : parcel.confidence_score >= 0.6
                      ? "text-yellow-400"
                      : "text-red-400"
                }`}>
                  {(parcel.confidence_score * 100).toFixed(1)}%
                </span>
              </div>

              {/* Confidence bar */}
              <div className="w-full bg-muted/30 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    parcel.confidence_score >= 0.8
                      ? "bg-emerald-500"
                      : parcel.confidence_score >= 0.6
                        ? "bg-yellow-500"
                        : "bg-red-500"
                  }`}
                  style={{ width: `${parcel.confidence_score * 100}%` }}
                />
              </div>

              {/* Action */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Action</span>
                <Badge variant="secondary" className="text-sm">
                  {parcel.action === "inspection" ? "🔍 Inspection" : "📤 Normal Line"}
                </Badge>
              </div>

              {/* Timestamp */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Detected At</span>
                <span className="text-sm font-mono">
                  {new Date(parcel.detected_at).toLocaleString()}
                </span>
              </div>

              {/* Track ID */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Track ID</span>
                <span className="text-sm font-mono bg-muted px-2 py-0.5 rounded">
                  T-{parcel.track_id}
                </span>
              </div>

              {/* Bounding Box */}
              <div className="flex items-center justify-between">
                <span className="text-sm text-muted-foreground">Bounding Box</span>
                <span className="text-xs font-mono text-muted-foreground">
                  ({parcel.bbox_x}, {parcel.bbox_y}, {parcel.bbox_w}, {parcel.bbox_h})
                </span>
              </div>

              {/* Back button */}
              <div className="pt-4">
                <Button
                  id="back-to-dashboard"
                  variant="outline"
                  onClick={() => router.push("/")}
                  className="w-full"
                >
                  ← Back to Dashboard
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}
