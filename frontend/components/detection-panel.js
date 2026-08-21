"use client";

import { useState } from "react";
import UploadPanel from "@/components/upload-panel";
import WebcamPanel from "@/components/webcam-panel";

const MODES = [
  { id: "webcam", label: "📹 Live Webcam", description: "Real-time detection" },
  { id: "upload", label: "📁 Upload Video", description: "Process a recording" },
];

export default function DetectionPanel({ onProcessingComplete }) {
  const [activeMode, setActiveMode] = useState("webcam");

  return (
    <div className="space-y-4">
      {/* Tab Switcher */}
      <div className="flex items-center gap-1 p-1 rounded-xl bg-muted/20 border border-muted-foreground/10 w-fit">
        {MODES.map((mode) => {
          const isActive = activeMode === mode.id;
          return (
            <button
              key={mode.id}
              id={`tab-${mode.id}`}
              onClick={() => setActiveMode(mode.id)}
              className={`
                relative px-5 py-2.5 rounded-lg text-sm font-medium
                transition-all duration-300 ease-out cursor-pointer
                ${
                  isActive
                    ? "bg-gradient-to-r from-purple-600/90 to-indigo-600/90 text-white shadow-lg shadow-purple-500/20"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/30"
                }
              `}
            >
              <span className="flex items-center gap-2">
                <span>{mode.label}</span>
                <span
                  className={`hidden sm:inline text-xs ${
                    isActive ? "text-white/70" : "text-muted-foreground/60"
                  }`}
                >
                  — {mode.description}
                </span>
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Panel */}
      <div className="transition-all duration-300">
        {activeMode === "webcam" ? (
          <WebcamPanel onProcessingComplete={onProcessingComplete} />
        ) : (
          <UploadPanel onProcessingComplete={onProcessingComplete} />
        )}
      </div>
    </div>
  );
}
