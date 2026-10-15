"use client";

import React, { useState } from "react";
import {
  Database,
  Calendar,
  Waves,
  MapPin,
  TrendingUp,
  FileText,
  Search,
  AlertTriangle,
} from "lucide-react";

export default function HistoricalView() {
  const [searchTerm, setSearchTerm] = useState("");

  const historicalEvents = [
    {
      id: "EVT_2022_09_05",
      name: "Bangalore Urban Basin Extreme Inundation",
      date: "September 05, 2022",
      rainfall_24h_mm: 131.6,
      max_depth_m: 2.45,
      affected_area_km2: 48.5,
      severity: "SEVERE",
      primary_valley: "Koramangala-Challaghatta & Bellandur Plain",
      notes: "Severe urban storm drainage breach across Mahadevapura and Outer Ring Road corridors.",
    },
    {
      id: "EVT_2022_08_30",
      name: "South Bangalore Cloudburst Inundation",
      date: "August 30, 2022",
      rainfall_24h_mm: 148.0,
      max_depth_m: 2.10,
      affected_area_km2: 32.0,
      severity: "SEVERE",
      primary_valley: "Vrishabhavathi Valley Catchment",
      notes: "Heavy flash inundation in low-lying residential layouts along Vrishabhavathi basin.",
    },
    {
      id: "EVT_2020_10_15",
      name: "Post-Monsoon Cyclone Inundation Surge",
      date: "October 15, 2020",
      rainfall_24h_mm: 98.4,
      max_depth_m: 1.35,
      affected_area_km2: 24.2,
      severity: "HIGH",
      primary_valley: "Hebbal Valley Drainage Axis",
      notes: "Hebbal lake outfall channel overflow caused flooding in northern perimeter.",
    },
    {
      id: "EVT_2017_08_15",
      name: "Independence Day Convective Deluge",
      date: "August 15, 2017",
      rainfall_24h_mm: 128.5,
      max_depth_m: 1.90,
      affected_area_km2: 38.0,
      severity: "SEVERE",
      primary_valley: "K&C Valley & Koramangala 4th Block",
      notes: "Intense 3-hour storm overwhelmed storm water drains (SWD).",
    },
    {
      id: "EVT_2015_09_24",
      name: "Hulimavu Catchment Breach Event",
      date: "September 24, 2015",
      rainfall_24h_mm: 82.0,
      max_depth_m: 1.15,
      affected_area_km2: 14.8,
      severity: "MODERATE",
      primary_valley: "South Catchment Zone",
      notes: "Localized drainage backflow in low-lying residential clusters.",
    },
  ];

  const filtered = historicalEvents.filter(
    (e) =>
      e.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.primary_valley.toLowerCase().includes(searchTerm.toLowerCase()) ||
      e.notes.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-2xl glass-panel p-5">
        <div>
          <div className="flex items-center gap-2">
            <Database className="h-5 w-5 text-cyan-400" />
            <h2 className="text-lg font-bold text-white">Historical Flood & Rainfall Event Archives</h2>
          </div>
          <p className="text-xs text-slate-400">
            Validated post-disaster flood inundation events used for ground-truth calibration and model validation
          </p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search event, valley, or notes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full rounded-xl bg-slate-900 border border-slate-700 pl-9 pr-4 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-cyan-500 focus:outline-none"
          />
        </div>
      </div>

      {/* Historical Event Cards / Table */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {filtered.map((evt) => (
          <div key={evt.id} className="rounded-2xl glass-panel p-5 space-y-3.5 border border-slate-800 hover:border-slate-700 transition-all shadow-xl">
            <div className="flex items-start justify-between border-b border-slate-800 pb-3">
              <div>
                <span className="text-[10px] font-mono text-cyan-400 uppercase tracking-wider">{evt.id}</span>
                <h3 className="text-sm font-bold text-slate-100">{evt.name}</h3>
                <div className="flex items-center gap-1.5 text-xs text-slate-400 mt-0.5">
                  <Calendar className="h-3.5 w-3.5 text-slate-500" />
                  <span>{evt.date}</span>
                </div>
              </div>
              <span
                className={`rounded px-2.5 py-0.5 text-[10px] font-bold uppercase ${
                  evt.severity === "SEVERE"
                    ? "bg-red-500/20 text-red-400 border border-red-500/30"
                    : "bg-orange-500/20 text-orange-400 border border-orange-500/30"
                }`}
              >
                {evt.severity}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-2 text-center text-xs">
              <div className="rounded-xl bg-slate-900/80 p-2.5 border border-slate-800">
                <div className="text-[10px] text-slate-400">Peak 24h Rain</div>
                <div className="font-bold text-cyan-400 text-sm mt-0.5">{evt.rainfall_24h_mm} mm</div>
              </div>
              <div className="rounded-xl bg-slate-900/80 p-2.5 border border-slate-800">
                <div className="text-[10px] text-slate-400">Max Depth</div>
                <div className="font-bold text-red-400 text-sm mt-0.5">{evt.max_depth_m} m</div>
              </div>
              <div className="rounded-xl bg-slate-900/80 p-2.5 border border-slate-800">
                <div className="text-[10px] text-slate-400">Affected Area</div>
                <div className="font-bold text-amber-400 text-sm mt-0.5">{evt.affected_area_km2} km²</div>
              </div>
            </div>

            <div className="space-y-1 text-xs">
              <div className="flex items-center gap-1.5 text-slate-300">
                <MapPin className="h-3.5 w-3.5 text-blue-400 shrink-0" />
                <span className="font-medium text-slate-400">Catchment:</span>
                <span className="font-semibold text-slate-200">{evt.primary_valley}</span>
              </div>
              <p className="text-xs text-slate-400 leading-relaxed bg-slate-900/40 p-2.5 rounded-lg border border-slate-800/60">
                {evt.notes}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
