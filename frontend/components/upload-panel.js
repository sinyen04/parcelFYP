"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { uploadVideo, fetchVideoStatus, getVideoStreamUrl } from "@/lib/api-client";

export default function UploadPanel({ onProcessingComplete }) {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [videoId, setVideoId] = useState(null);
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  // Poll for video status when processing
  useEffect(() => {
    if (!videoId || status === "completed" || status === "failed") return;

    const interval = setInterval(async () => {
      try {
        const data = await fetchVideoStatus(videoId);
        setStatus(data.status);
        if (data.status === "completed" || data.status === "failed") {
          clearInterval(interval);
          if (data.status === "completed" && onProcessingComplete) {
            onProcessingComplete();
          }
        }
      } catch (err) {
        console.error("Status poll failed:", err);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [videoId, status, onProcessingComplete]);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setStatus(null);
    setVideoId(null);

    try {
      const data = await uploadVideo(file);
      setVideoId(data.id);
      setStatus(data.status);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
    }
  };

  const statusVariant = {
    pending: "secondary",
    processing: "default",
    completed: "default",
    failed: "destructive",
  };

  const statusColors = {
    pending: "bg-yellow-500/20 text-yellow-400 border-yellow-500/40",
    processing: "bg-blue-500/20 text-blue-400 border-blue-500/40 animate-pulse",
    completed: "bg-emerald-500/20 text-emerald-400 border-emerald-500/40",
    failed: "bg-red-500/20 text-red-400 border-red-500/40",
  };

  return (
    <Card
      id="upload-panel"
      className="border-dashed border-2 border-muted-foreground/20 bg-gradient-to-br from-purple-500/5 to-indigo-500/5"
    >
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-xl">🎥</span>
          Upload Video
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col sm:flex-row gap-3">
          <Input
            id="video-file-input"
            ref={fileRef}
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="flex-1 file:mr-4 file:py-1 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90 cursor-pointer"
          />
          <Button
            id="upload-button"
            onClick={handleUpload}
            disabled={!file || uploading}
            className="min-w-[120px] bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg shadow-purple-500/25 transition-all duration-300"
          >
            {uploading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Uploading…
              </span>
            ) : (
              "Upload & Process"
            )}
          </Button>
        </div>

        {status && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-muted-foreground">Status:</span>
            <Badge className={`${statusColors[status] || ""} border`}>
              {status === "processing" && "⏳ "}
              {status === "completed" && "✅ "}
              {status === "failed" && "❌ "}
              {status?.toUpperCase()}
            </Badge>
          </div>
        )}

        {error && (
          <p className="text-sm text-red-400 bg-red-500/10 rounded-md px-3 py-2">
            ❌ {error}
          </p>
        )}

        {status === "processing" && videoId && (
          <div className="mt-4 rounded-xl overflow-hidden border border-muted-foreground/20 shadow-2xl bg-black">
            <div className="bg-muted/30 px-3 py-2 text-xs text-muted-foreground flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                LIVE PROCESSING
              </span>
            </div>
            <img 
              src={getVideoStreamUrl(videoId)} 
              alt="Live video processing stream" 
              className="w-full h-auto aspect-video object-contain"
            />
          </div>
        )}
      </CardContent>
    </Card>
  );
}
