"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ShieldAlert,
  SlidersHorizontal,
  ChevronRight,
  Info,
  MapPin,
} from "lucide-react";

interface AlertItem {
  id: string;
  alert_type: string;
  severity: string;
  title: string;
  description: string;
  is_active: boolean;
  created_at: string;
  acknowledged_at?: string;
}

interface AlertsDrawerProps {
  alerts: AlertItem[];
  onAcknowledge: (id: string) => Promise<void>;
}

export default function AlertsDrawer({ alerts, onAcknowledge }: AlertsDrawerProps) {
  const [filterSeverity, setFilterSeverity] = useState<string>("ALL");
  const [filterActiveOnly, setFilterActiveOnly] = useState<boolean>(false);
  const [acknowledgingId, setAcknowledgingId] = useState<string | null>(null);

  const filtered = alerts.filter((a) => {
    if (filterSeverity !== "ALL" && a.severity !== filterSeverity) return false;
    if (filterActiveOnly && !a.is_active) return false;
    return true;
  });

  const handleAck = async (id: string) => {
    setAcknowledgingId(id);
    try {
      await onAcknowledge(id);
    } finally {
      setAcknowledgingId(null);
    }
  };

  return (
    <div className="flex h-full flex-col gap-4 rounded-2xl glass-panel p-6 shadow-2xl">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className="h-5 w-5 text-red-400" />
            <h2 className="text-lg font-bold text-white">Emergency Warning & Alert Command</h2>
          </div>
          <p className="text-xs text-slate-400">
            Automated threshold & AI-triggered flood warning dispatch center
          </p>
        </div>

        {/* Severity Filters */}
        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="text-slate-500 flex items-center gap-1 font-medium">
            <SlidersHorizontal className="h-3.5 w-3.5" /> Filter:
          </span>
          {["ALL", "CRITICAL", "HIGH", "MODERATE"].map((sev) => (
            <button
              key={sev}
              onClick={() => setFilterSeverity(sev)}
              className={`rounded-lg px-3 py-1 font-semibold transition-all ${
                filterSeverity === sev
                  ? sev === "CRITICAL"
                    ? "bg-red-500 text-white"
                    : sev === "HIGH"
                    ? "bg-orange-500 text-white"
                    : "bg-cyan-600 text-white"
                  : "bg-slate-800 text-slate-400 hover:text-white"
              }`}
            >
              {sev}
            </button>
          ))}

          <button
            onClick={() => setFilterActiveOnly((prev) => !prev)}
            className={`rounded-lg px-3 py-1 font-semibold border ${
              filterActiveOnly
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
                : "bg-slate-800/60 text-slate-400 border-slate-700 hover:text-white"
            }`}
          >
            {filterActiveOnly ? "Active Only" : "All Statuses"}
          </button>
        </div>
      </div>

      {/* Alert Feed List */}
      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {filtered.length === 0 ? (
          <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-dashed border-slate-800 p-8 text-center">
            <CheckCircle2 className="h-10 w-10 text-emerald-400 mb-2" />
            <h3 className="text-sm font-bold text-slate-200">No Warnings Matching Filters</h3>
            <p className="text-xs text-slate-500 mt-1">All monitoring stations and catchment areas within normal safety parameters.</p>
          </div>
        ) : (
          filtered.map((alert) => {
            const isCritical = alert.severity === "CRITICAL";
            const isHigh = alert.severity === "HIGH";

            return (
              <div
                key={alert.id}
                className={`relative flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl p-4 transition-all border ${
                  alert.is_active
                    ? isCritical
                      ? "bg-red-950/20 border-red-500/40 shadow-lg shadow-red-500/5"
                      : isHigh
                      ? "bg-orange-950/20 border-orange-500/40"
                      : "bg-amber-950/20 border-amber-500/40"
                    : "bg-slate-900/40 border-slate-800/80 opacity-70"
                }`}
              >
                <div className="flex items-start gap-3.5">
                  <div
                    className={`mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${
                      isCritical
                        ? "bg-red-500/20 text-red-400 border border-red-500/30"
                        : isHigh
                        ? "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                        : "bg-amber-500/20 text-amber-400 border border-amber-500/30"
                    }`}
                  >
                    <AlertTriangle className="h-5 w-5" />
                  </div>

                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-100">{alert.title}</h4>
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                          isCritical
                            ? "bg-red-500 text-white shadow-sm shadow-red-500/50"
                            : isHigh
                            ? "bg-orange-500 text-white"
                            : "bg-amber-500 text-slate-950"
                        }`}
                      >
                        {alert.severity}
                      </span>
                      {alert.is_active ? (
                        <span className="flex items-center gap-1 rounded bg-red-500/10 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/20">
                          <span className="h-1.5 w-1.5 rounded-full bg-red-400 animate-pulse"></span>
                          ACTIVE
                        </span>
                      ) : (
                        <span className="rounded bg-slate-800 px-2 py-0.5 text-[10px] font-bold text-slate-400">
                          ACKNOWLEDGED
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-300 leading-relaxed max-w-2xl">{alert.description}</p>

                    <div className="flex items-center gap-3 pt-1 text-[11px] text-slate-400 font-mono">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3 text-cyan-400" />
                        {new Date(alert.created_at).toLocaleString()}
                      </span>
                      <span>•</span>
                      <span className="text-slate-400 uppercase font-semibold">{alert.alert_type}</span>
                    </div>
                  </div>
                </div>

                {/* Acknowledge Button */}
                {alert.is_active && (
                  <button
                    disabled={acknowledgingId === alert.id}
                    onClick={() => handleAck(alert.id)}
                    className="shrink-0 rounded-xl bg-slate-800 hover:bg-emerald-600 px-4 py-2 text-xs font-bold text-slate-200 hover:text-white transition-all duration-200 border border-slate-700 hover:border-emerald-500 shadow-sm"
                  >
                    {acknowledgingId === alert.id ? "Acknowledging..." : "Acknowledge Warning"}
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
