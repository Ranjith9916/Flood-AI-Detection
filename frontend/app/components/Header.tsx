"use client";

import React, { useEffect, useState } from "react";
import {
  CloudRain,
  MapPin,
  Search,
  Layers,
  BarChart3,
  ShieldAlert,
  Cpu,
  History,
  Sparkles,
  Wifi,
  Clock,
  Radio,
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  activeAlertCount: number;
  onAlertClick: () => void;
  onOpenSimulator?: () => void;
  systemStatus?: any;
  wsConnected?: boolean;
}

export default function Header({
  activeTab,
  setActiveTab,
  activeAlertCount,
  onAlertClick,
  onOpenSimulator,
  systemStatus,
  wsConnected = true,
}: HeaderProps) {
  const [currentTime, setCurrentTime] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setCurrentTime(
        now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          second: "2-digit",
          hour12: true,
        })
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  const navTabs = [
    { id: "overview", label: "Weather & Hydro", icon: CloudRain },
    { id: "gis", label: "Radar & Flood Map", icon: Layers },
    { id: "analytics", label: "Hyetographs", icon: BarChart3 },
    { id: "alerts", label: "Disaster Alerts", icon: ShieldAlert, badge: activeAlertCount },
    { id: "models", label: "AI Registry", icon: Cpu },
    { id: "history", label: "Historic Events", icon: History },
  ];

  return (
    <header className="sticky top-0 z-50 bg-[#0b121e]/90 backdrop-blur-xl border-b border-white/10 px-4 md:px-8 py-3 transition-all">
      <div className="max-w-7xl mx-auto flex flex-col lg:flex-row items-center justify-between gap-3">
        {/* Left: Google Weather Branding & Search Location Pill */}
        <div className="flex items-center gap-4 w-full lg:w-auto justify-between lg:justify-start">
          {/* Brand Logo */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-500 to-cyan-400 p-2 flex items-center justify-center shadow-lg shadow-blue-500/20 flex-shrink-0">
              <CloudRain className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <span className="text-base font-bold tracking-tight text-white">Google</span>
                <span className="text-base font-medium text-[#8ab4f8]">Weather & Flood AI</span>
              </div>
              <p className="text-[11px] text-slate-400 font-normal">
                National Early Warning & Inundation System
              </p>
            </div>
          </div>

          {/* Location Chip / Search Bar */}
          <div className="hidden sm:flex items-center gap-2 bg-[#162136] border border-white/10 rounded-full px-3.5 py-1.5 text-xs text-slate-200 hover:border-blue-400/50 transition-all shadow-inner">
            <MapPin className="w-3.5 h-3.5 text-[#8ab4f8]" />
            <span className="font-medium">Chennai, Tamil Nadu</span>
            <span className="text-slate-500">•</span>
            <span className="text-blue-300 font-semibold">29°C Heavy Rain</span>
          </div>
        </div>

        {/* Center: Google Material Pill Navigation Tabs */}
        <nav className="flex items-center gap-1 bg-[#131d30] p-1 rounded-full border border-white/10 overflow-x-auto max-w-full">
          {navTabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                id={`tab-${tab.id}`}
                onClick={() => setActiveTab(tab.id)}
                className={`google-pill ${isActive ? "google-pill-active" : "google-pill-inactive"} cursor-pointer text-xs`}
              >
                <Icon className={`w-3.5 h-3.5 ${isActive ? "text-[#0b121e]" : "text-slate-400"}`} />
                <span>{tab.label}</span>
                {tab.badge !== undefined && tab.badge > 0 && (
                  <span
                    onClick={(e) => {
                      e.stopPropagation();
                      onAlertClick();
                    }}
                    className={`ml-1 px-1.5 py-0.2 rounded-full text-[10px] font-bold ${
                      isActive ? "bg-red-600 text-white" : "bg-red-500/30 text-red-400 border border-red-500/40 animate-pulse"
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Right: Simulation Quick Launcher & Real-Time Status */}
        <div className="hidden lg:flex items-center gap-3">
          {/* What-If Simulator Trigger Button */}
          {onOpenSimulator && (
            <button
              onClick={onOpenSimulator}
              className="google-pill bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white text-xs font-semibold shadow-md shadow-blue-500/20 active:scale-95 transition-all cursor-pointer"
            >
              <Sparkles className="w-3.5 h-3.5 text-yellow-300" />
              <span>Simulator</span>
            </button>
          )}

          {/* WebSocket Status Indicator */}
          <div className="flex items-center gap-2 bg-[#162136] border border-white/10 rounded-full px-3 py-1.5 text-xs">
            <span className={`w-2 h-2 rounded-full ${wsConnected ? "bg-emerald-400 shadow-sm shadow-emerald-400 animate-pulse" : "bg-amber-400"}`} />
            <span className="text-slate-300 font-mono text-[11px]">{currentTime}</span>
          </div>
        </div>
      </div>
    </header>
  );
}
