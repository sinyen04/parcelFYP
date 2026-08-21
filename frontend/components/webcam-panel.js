"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getWebcamWsUrl } from "@/lib/api-client";

export default function WebcamPanel({ onProcessingComplete }) {
  const [isStreaming, setIsStreaming] = useState(false);
  const [permissionDenied, setPermissionDenied] = useState(false);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ total_confirmed: 0, damaged: 0, undamaged: 0 });
  const [detections, setDetections] = useState([]);
  const [frameCount, setFrameCount] = useState(0);
  const [sessionSaved, setSessionSaved] = useState(false);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const displayRef = useRef(null);
  const wsRef = useRef(null);
  const streamRef = useRef(null);
  const intervalRef = useRef(null);
  const isStreamingRef = useRef(false);

  // Keep the ref in sync with state so the interval callback sees the latest value
  useEffect(() => {
    isStreamingRef.current = isStreaming;
  }, [isStreaming]);

  const stopWebcam = useCallback(() => {
    // Stop the capture interval
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    // Stop all media tracks
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }

    // Clear the video element
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    setIsStreaming(false);
  }, []);

  const startWebcam = useCallback(async () => {
    setError(null);
    setPermissionDenied(false);
    setSessionSaved(false);
    setStats({ total_confirmed: 0, damaged: 0, undamaged: 0 });
    setDetections([]);
    setFrameCount(0);

    // 1. Request camera permission
    let mediaStream;
    try {
      mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 } },
      });
    } catch (err) {
      if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
        setPermissionDenied(true);
        setError("Camera permission was denied. Please allow camera access and try again.");
      } else if (err.name === "NotFoundError") {
        setError("No camera found. Please connect a webcam and try again.");
      } else {
        setError(`Camera error: ${err.message}`);
      }
      return;
    }

    streamRef.current = mediaStream;

    // 2. Set up video element
    if (videoRef.current) {
      videoRef.current.srcObject = mediaStream;
      await videoRef.current.play();
    }

    // 3. Connect WebSocket
    const wsUrl = getWebcamWsUrl();
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsStreaming(true);

      // 4. Start capturing frames at ~5 FPS
      const canvas = canvasRef.current;
      const video = videoRef.current;

      intervalRef.current = setInterval(() => {
        if (!isStreamingRef.current || !video || !canvas || ws.readyState !== WebSocket.OPEN) return;

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        const ctx = canvas.getContext("2d");
        ctx.drawImage(video, 0, 0);

        canvas.toBlob(
          (blob) => {
            if (blob && ws.readyState === WebSocket.OPEN) {
              ws.send(blob);
            }
          },
          "image/jpeg",
          0.8
        );
      }, 200); // 5 FPS
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Display annotated frame
        if (data.annotated_frame && displayRef.current) {
          displayRef.current.src = `data:image/jpeg;base64,${data.annotated_frame}`;
        }

        // Update stats
        if (data.stats) {
          setStats(data.stats);
        }

        // Update detections
        if (data.detections) {
          setDetections(data.detections);
        }

        if (data.frame_index !== undefined) {
          setFrameCount(data.frame_index + 1);
        }
      } catch (err) {
        console.error("Failed to parse WebSocket message:", err);
      }
    };

    ws.onerror = () => {
      setError("WebSocket connection error. Is the backend running?");
      stopWebcam();
    };

    ws.onclose = () => {
      if (isStreamingRef.current) {
        setSessionSaved(true);
        stopWebcam();
        if (onProcessingComplete) {
          onProcessingComplete();
        }
      }
    };
  }, [stopWebcam, onProcessingComplete]);

  const handleStop = useCallback(() => {
    setSessionSaved(true);
    stopWebcam();
    if (onProcessingComplete) {
      onProcessingComplete();
    }
  }, [stopWebcam, onProcessingComplete]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopWebcam();
    };
  }, [stopWebcam]);

  return (
    <Card
      id="webcam-panel"
      className="border-dashed border-2 border-muted-foreground/20 bg-gradient-to-br from-cyan-500/5 to-blue-500/5"
    >
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <span className="text-xl">📹</span>
          Live Webcam Detection
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Controls */}
        <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-center">
          {!isStreaming ? (
            <Button
              id="start-webcam-button"
              onClick={startWebcam}
              className="min-w-[160px] bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-700 hover:to-blue-700 text-white shadow-lg shadow-cyan-500/25 transition-all duration-300"
            >
              <span className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" />
                  <rect x="2" y="6" width="14" height="12" rx="2" />
                </svg>
                Start Webcam
              </span>
            </Button>
          ) : (
            <Button
              id="stop-webcam-button"
              onClick={handleStop}
              variant="destructive"
              className="min-w-[160px] bg-gradient-to-r from-red-600 to-rose-600 hover:from-red-700 hover:to-rose-700 shadow-lg shadow-red-500/25 transition-all duration-300"
            >
              <span className="flex items-center gap-2">
                <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
                Stop & Save
              </span>
            </Button>
          )}

          {/* Live Stats */}
          {isStreaming && (
            <div className="flex items-center gap-3 flex-wrap">
              <Badge className="bg-emerald-500/20 text-emerald-400 border border-emerald-500/40">
                ✅ Confirmed: {stats.total_confirmed}
              </Badge>
              <Badge className="bg-red-500/20 text-red-400 border border-red-500/40">
                ⚠️ Damaged: {stats.damaged}
              </Badge>
              <Badge className="bg-blue-500/20 text-blue-400 border border-blue-500/40">
                📦 Undamaged: {stats.undamaged}
              </Badge>
              <Badge className="bg-gray-500/20 text-gray-400 border border-gray-500/40">
                🖼️ Frames: {frameCount}
              </Badge>
            </div>
          )}
        </div>

        {/* Permission denied error */}
        {permissionDenied && (
          <div className="rounded-md bg-yellow-500/10 border border-yellow-500/30 px-4 py-3 text-sm text-yellow-400">
            <p className="font-semibold mb-1">📷 Camera Permission Required</p>
            <p>
              Your browser blocked camera access. To fix this:
            </p>
            <ol className="list-decimal list-inside mt-1 space-y-0.5 text-yellow-400/80">
              <li>Click the camera icon in your browser's address bar</li>
              <li>Select "Allow" for camera access</li>
              <li>Click "Start Webcam" again</li>
            </ol>
          </div>
        )}

        {/* General error */}
        {error && !permissionDenied && (
          <p className="text-sm text-red-400 bg-red-500/10 rounded-md px-3 py-2">
            ❌ {error}
          </p>
        )}

        {/* Session saved message */}
        {sessionSaved && !isStreaming && stats.total_confirmed > 0 && (
          <div className="rounded-md bg-emerald-500/10 border border-emerald-500/30 px-4 py-3 text-sm text-emerald-400">
            <p className="font-semibold">✅ Session Saved!</p>
            <p>
              Detected {stats.total_confirmed} parcel(s) — {stats.damaged} damaged, {stats.undamaged} undamaged.
              Results have been saved and are visible in the parcel list below.
            </p>
          </div>
        )}

        {/* Hidden video element for camera capture */}
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          style={{ display: "none" }}
        />
        {/* Hidden canvas for frame capture */}
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {/* Live Feed Display */}
        {isStreaming && (
          <div className="mt-2 rounded-xl overflow-hidden border border-muted-foreground/20 shadow-2xl bg-black">
            <div className="bg-muted/30 px-3 py-2 text-xs text-muted-foreground flex items-center justify-between">
              <span className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
                </span>
                LIVE WEBCAM
              </span>
              <span className="text-muted-foreground/60">
                {detections.length} detection(s) in view
              </span>
            </div>
            <img
              ref={displayRef}
              alt="Live webcam detection feed"
              className="w-full h-auto aspect-video object-contain"
            />
          </div>
        )}

        {/* Idle state: no stream */}
        {!isStreaming && !sessionSaved && !error && (
          <div className="rounded-xl border-2 border-dashed border-muted-foreground/10 bg-muted/5 flex flex-col items-center justify-center py-12 text-muted-foreground/40">
            <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className="mb-3 opacity-40">
              <path d="m16 13 5.223 3.482a.5.5 0 0 0 .777-.416V7.87a.5.5 0 0 0-.752-.432L16 10.5" />
              <rect x="2" y="6" width="14" height="12" rx="2" />
            </svg>
            <p className="text-sm">Click "Start Webcam" to begin live detection</p>
            <p className="text-xs mt-1 opacity-60">Your browser will ask for camera permission</p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
