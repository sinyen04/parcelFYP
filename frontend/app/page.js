"use client";

import { useState, useCallback, useEffect } from "react";
import { Button } from "@/components/ui/button";
import SummaryCards from "@/components/summary-cards";
import UploadPanel from "@/components/upload-panel";
import ParcelList from "@/components/parcel-list";
import LoginForm from "@/components/login-form";
import { logout, getToken } from "@/lib/api-client";

export default function DashboardPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  // Check for existing token on mount
  useEffect(() => {
    const token = getToken();
    if (token) {
      setIsAuthenticated(true);
    }
  }, []);

  const handleProcessingComplete = useCallback(() => {
    // Trigger a refresh of all data components
    setRefreshKey((k) => k + 1);
  }, []);

  const handleLogout = async () => {
    await logout();
    setIsAuthenticated(false);
  };

  // Show login form if not authenticated
  if (!isAuthenticated) {
    return <LoginForm onLoginSuccess={() => setIsAuthenticated(true)} />;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950">
      {/* Background decoration */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-purple-500/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-indigo-500/3 rounded-full blur-3xl" />
      </div>

      {/* Header */}
      <header className="sticky top-0 z-50 backdrop-blur-xl bg-background/60 border-b border-border/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-3xl">📦</span>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-purple-400 via-indigo-400 to-blue-400 bg-clip-text text-transparent">
                Parcel Detection System
              </h1>
              <p className="text-xs text-muted-foreground">
                AI-Powered Condition Analysis
              </p>
            </div>
          </div>
          <Button
            id="logout-button"
            variant="outline"
            onClick={handleLogout}
            className="border-muted-foreground/20 hover:bg-destructive/10 hover:text-red-400 hover:border-red-500/30 transition-all duration-300"
          >
            Log Out
          </Button>
        </div>
      </header>

      {/* Main Content */}
      <main className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {/* Summary Cards */}
        <section id="summary-section">
          <SummaryCards refreshTrigger={refreshKey} />
        </section>

        {/* Upload Panel */}
        <section id="upload-section">
          <UploadPanel onProcessingComplete={handleProcessingComplete} />
        </section>

        {/* Parcel Lists */}
        <section id="parcel-lists-section" className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <ParcelList condition="damaged" refreshTrigger={refreshKey} />
          <ParcelList condition="undamaged" refreshTrigger={refreshKey} />
        </section>
      </main>

      {/* Footer */}
      <footer className="relative z-10 text-center py-6 text-xs text-muted-foreground border-t border-border/20">
        Parcel Condition Detection System &copy; {new Date().getFullYear()}
      </footer>
    </div>
  );
}
