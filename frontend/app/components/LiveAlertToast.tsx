"use client";

import React, { useState } from "react";
import { ShieldAlert, AlertTriangle, X, CheckCircle, Volume2, VolumeX, ArrowRight } from "lucide-react";

interface LiveAlertToastProps {
  alert: {
    id: string;
    title: string;
    description: string;
    severity: string;
    alert_type?: string;
  } | null;
  onAcknowledge: (id: string) => void;
  onClose: () => void;
  onViewMap?: () => void;
}

export default function LiveAlertToast({
  alert,
  onAcknowledge,
  onClose,
  onViewMap,
}: LiveAlertToastProps) {
  const [muted, setMuted] = useState(false);

  if (!alert) return null;

  const isCritical = alert.severity === "CRITICAL" || alert.severity === "EXTREME" || alert.severity === "SEVERE_WARNING";

  return (
    <div className="fixed top-18 right-6 z-50 max-w-lg w-full animate-bounce transition-all">
      <div
        className={`google-card p-4 md:p-5 rounded-3xl border shadow-2xl backdrop-blur-2xl ${
          isCritical
            ? "bg-[#2a0e14]/90 border-red-500/50 shadow-red-950/50"
            : "bg-[#2a1d0b]/90 border-amber-500/50 shadow-amber-950/50"
        }`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <div
              className={`w-10 h-10 rounded-2xl flex items-center justify-center flex-shrink-0 ${
                isCritical ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
              }`}
            >
              <ShieldAlert className="w-6 h-6 animate-pulse" />
            </div>

            <div>
              <div className="flex items-center gap-2">
                <span
                  className={`text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full ${
                    isCritical ? "bg-red-500 text-white" : "bg-amber-500 text-black"
                  }`}
                >
                  {alert.severity} EARLY WARNING
                </span>
                <span className="text-xs text-slate-400">Live Broadcast</span>
              </div>
              <h4 className="text-sm font-bold text-white mt-1 leading-snug">{alert.title}</h4>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={() => setMuted(!muted)}
              className="p-1.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
              title={muted ? "Unmute Alerts" : "Mute Sound"}
            >
              {muted ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4 text-blue-400" />}
            </button>
            <button
              onClick={onClose}
              className="p-1.5 rounded-full hover:bg-white/10 text-slate-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <p className="text-xs text-slate-300 mt-2.5 line-clamp-2 leading-relaxed pl-13">
          {alert.description}
        </p>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2 mt-4 pt-3 border-t border-white/10">
          {onViewMap && (
            <button
              onClick={() => {
                onViewMap();
                onClose();
              }}
              className="px-3.5 py-1.5 rounded-full bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 hover:text-white flex items-center gap-1.5 transition-all cursor-pointer"
            >
              <span>View On Map</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}

          <button
            onClick={() => {
              onAcknowledge(alert.id);
              onClose();
            }}
            className="px-4 py-1.5 rounded-full bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs flex items-center gap-1.5 shadow-md transition-all cursor-pointer active:scale-95"
          >
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Acknowledge</span>
          </button>
        </div>
      </div>
    </div>
  );
}
