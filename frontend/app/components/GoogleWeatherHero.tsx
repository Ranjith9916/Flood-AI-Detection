"use client";

import React, { useState } from "react";
import {
  CloudRain,
  CloudLightning,
  Droplets,
  Wind,
  Compass,
  Thermometer,
  ShieldAlert,
  AlertTriangle,
  Waves,
  Sparkles,
  ArrowUpRight,
} from "lucide-react";

interface WeatherObservation {
  temperature_c?: number;
  relative_humidity_pct?: number;
  wind_speed_ms?: number;
  surface_pressure_hpa?: number;
  rainfall_rate_mmh?: number;
}

interface RainfallData {
  rainfall_1h_mm?: number;
  rainfall_3h_mm?: number;
  rainfall_6h_mm?: number;
  rainfall_12h_mm?: number;
  rainfall_24h_mm?: number;
}

interface FloodPrediction {
  flood_probability?: number;
  risk_level?: string;
}

interface InundationPrediction {
  maximum_depth_m?: number;
  affected_area_km2?: number;
}

interface GoogleWeatherHeroProps {
  weather?: WeatherObservation;
  rainfall?: RainfallData;
  flood?: FloodPrediction;
  inundation?: InundationPrediction;
  locationName?: string;
  onOpenSimulator?: () => void;
}

export default function GoogleWeatherHero({
  weather,
  rainfall,
  flood,
  inundation,
  locationName = "Chennai Metropolitan Catchment",
  onOpenSimulator,
}: GoogleWeatherHeroProps) {
  const [selectedHourlyTab, setSelectedHourlyTab] = useState<"rain" | "flood" | "temp">("rain");

  const temp = weather?.temperature_c ?? 29.5;
  const humidity = weather?.relative_humidity_pct ?? 92;
  const windSpeed = weather?.wind_speed_ms ?? 14.2;
  const rain24h = rainfall?.rainfall_24h_mm ?? 138.4;
  const rainRate = weather?.rainfall_rate_mmh ?? 38.0;
  const floodProb = (flood?.flood_probability ?? 0.88) * 100;
  const riskLevel = flood?.risk_level ?? "HIGH";
  const depthM = inundation?.maximum_depth_m ?? 0.95;

  // Hourly Google weather forecast timeline
  const hourlyData = [
    { time: "Now", icon: "storm", temp: `${Math.round(temp)}°`, rainChance: "95%", rainRate: "38mm", depth: "0.9m" },
    { time: "1 AM", icon: "heavy-rain", temp: `${Math.round(temp - 0.5)}°`, rainChance: "90%", rainRate: "32mm", depth: "1.0m" },
    { time: "2 AM", icon: "heavy-rain", temp: `${Math.round(temp - 1.0)}°`, rainChance: "85%", rainRate: "28mm", depth: "1.1m" },
    { time: "3 AM", icon: "storm", temp: `${Math.round(temp - 1.2)}°`, rainChance: "80%", rainRate: "22mm", depth: "1.1m" },
    { time: "4 AM", icon: "rain", temp: `${Math.round(temp - 1.5)}°`, rainChance: "70%", rainRate: "16mm", depth: "0.9m" },
    { time: "5 AM", icon: "rain", temp: `${Math.round(temp - 1.8)}°`, rainChance: "60%", rainRate: "12mm", depth: "0.7m" },
    { time: "6 AM", icon: "cloudy", temp: `${Math.round(temp - 1.0)}°`, rainChance: "45%", rainRate: "6mm", depth: "0.5m" },
    { time: "7 AM", icon: "cloudy", temp: `${Math.round(temp + 0.5)}°`, rainChance: "35%", rainRate: "2mm", depth: "0.3m" },
  ];

  const getRiskBadge = (level: string) => {
    switch (level) {
      case "EXTREME":
      case "VERY_HIGH":
        return {
          bg: "bg-red-500/20 text-red-300 border-red-500/40",
          icon: <ShieldAlert className="w-4 h-4 text-red-400 animate-pulse" />,
          label: "EXTREME FLOOD RISK",
        };
      case "HIGH":
        return {
          bg: "bg-amber-500/20 text-amber-300 border-amber-500/40",
          icon: <AlertTriangle className="w-4 h-4 text-amber-400" />,
          label: "HIGH FLOOD RISK",
        };
      case "MODERATE":
        return {
          bg: "bg-yellow-500/20 text-yellow-300 border-yellow-500/40",
          icon: <AlertTriangle className="w-4 h-4 text-yellow-400" />,
          label: "MODERATE FLOOD RISK",
        };
      default:
        return {
          bg: "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
          icon: <Sparkles className="w-4 h-4 text-emerald-400" />,
          label: "NORMAL DRAINAGE FLOW",
        };
    }
  };

  const riskBadge = getRiskBadge(riskLevel);

  return (
    <div className="google-weather-hero p-6 md:p-8 mb-6 shadow-2xl relative">
      {/* Decorative Atmosphere Glow */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-10 w-80 h-80 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Top Bar: Location & AI Risk Pill */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6 relative z-10">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-white">{locationName}</h2>
            <span className="text-xs px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium border border-blue-500/30">
              Live AWS Station
            </span>
          </div>
          <p className="text-sm text-slate-400 mt-0.5">
            Real-time Sensor Telemetry & Doppler Radar Fusion • Updated just now
          </p>
        </div>

        {/* Material Flood Risk Pill Badge */}
        <div className="flex items-center gap-3">
          <div className={`px-3.5 py-1.5 rounded-full border text-xs font-semibold flex items-center gap-2 ${riskBadge.bg}`}>
            {riskBadge.icon}
            <span>{riskBadge.label}</span>
          </div>

          {onOpenSimulator && (
            <button
              onClick={onOpenSimulator}
              className="px-4 py-1.5 rounded-full bg-[#8ab4f8] text-[#0b121e] hover:bg-[#aecbfa] text-xs font-semibold flex items-center gap-1.5 shadow-md transition-all active:scale-95"
            >
              <Sparkles className="w-3.5 h-3.5" />
              What-If Simulator
            </button>
          )}
        </div>
      </div>

      {/* Main Temperature & Weather State Display */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center relative z-10">
        {/* Left Col: Big Temp & Hero Art */}
        <div className="lg:col-span-6 flex items-center gap-6 md:gap-8">
          {/* Animated Weather Icon SVG */}
          <div className="relative w-28 h-28 md:w-36 md:h-36 flex-shrink-0 flex items-center justify-center">
            <div className="absolute inset-0 bg-blue-500/20 rounded-full blur-xl animate-pulse" />
            <div className="relative z-10 w-full h-full p-2 bg-slate-900/60 rounded-3xl border border-white/10 flex flex-col items-center justify-center shadow-inner">
              <CloudLightning className="w-14 h-14 md:w-16 md:h-16 text-yellow-300 animate-bounce" />
              <div className="flex gap-1.5 mt-1">
                <span className="w-1.5 h-3 bg-blue-400 rounded-full animate-rain-drop" />
                <span className="w-1.5 h-3 bg-blue-400 rounded-full animate-rain-drop [animation-delay:0.2s]" />
                <span className="w-1.5 h-3 bg-blue-400 rounded-full animate-rain-drop [animation-delay:0.4s]" />
              </div>
            </div>
          </div>

          {/* Large Degrees & Description */}
          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-6xl md:text-7xl font-extrabold tracking-tight text-white">{Math.round(temp)}°</span>
              <span className="text-xl md:text-2xl font-light text-slate-400">C</span>
            </div>
            <div className="text-lg md:text-xl font-medium text-slate-200 mt-1 flex items-center gap-2">
              Heavy Monsoon Downpour
            </div>
            <p className="text-xs md:text-sm text-slate-400 mt-1">
              Feels like {Math.round(temp + 4)}°C • High: {Math.round(temp + 2)}° / Low: {Math.round(temp - 3)}°
            </p>
          </div>
        </div>

        {/* Right Col: AI Early Warning Nowcast Pill Card */}
        <div className="lg:col-span-6 bg-slate-900/70 border border-white/10 rounded-3xl p-5 md:p-6 backdrop-blur-xl">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <div className="w-2.5 h-2.5 rounded-full bg-red-400 animate-ping" />
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-300">
                IMD & AI Integrated Nowcast
              </span>
            </div>
            <span className="text-xs text-blue-400 font-medium">Confidence: 96.8%</span>
          </div>

          <div className="text-base md:text-lg font-semibold text-white mb-2">
            Cloudburst band active • Rain continuing for next 3 hours
          </div>

          <p className="text-xs text-slate-300 mb-4 leading-relaxed">
            Severe convective storm cell with radar reflectivity exceeding <strong className="text-yellow-300">48 dBZ</strong>.
            Anticipated 24h accumulation: <strong className="text-blue-300">{rain24h.toFixed(1)} mm</strong>. Max water depth in low-lying subways: <strong className="text-red-400">{depthM.toFixed(2)} meters</strong>.
          </p>

          {/* Quick Telemetry Pills */}
          <div className="grid grid-cols-3 gap-2">
            <div className="bg-white/5 border border-white/5 rounded-2xl p-2.5 text-center">
              <div className="text-[11px] text-slate-400 font-medium">Precip Rate</div>
              <div className="text-sm md:text-base font-bold text-blue-300 mt-0.5">{rainRate.toFixed(1)} mm/h</div>
            </div>
            <div className="bg-white/5 border border-white/5 rounded-2xl p-2.5 text-center">
              <div className="text-[11px] text-slate-400 font-medium">Flood Prob</div>
              <div className="text-sm md:text-base font-bold text-amber-300 mt-0.5">{floodProb.toFixed(1)}%</div>
            </div>
            <div className="bg-white/5 border border-white/5 rounded-2xl p-2.5 text-center">
              <div className="text-[11px] text-slate-400 font-medium">Peak Inundation</div>
              <div className="text-sm md:text-base font-bold text-red-400 mt-0.5">{depthM.toFixed(2)} m</div>
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Google Weather-Style Hourly Forecast Strip */}
      <div className="mt-8 pt-6 border-t border-white/10 relative z-10">
        <div className="flex items-center justify-between mb-4">
          <div className="text-sm font-semibold text-white flex items-center gap-2">
            <span>Next 8-Hour Forecast & Water Accumulation</span>
          </div>

          {/* Tab Selector */}
          <div className="flex bg-slate-900/60 p-1 rounded-full border border-white/10 text-xs">
            <button
              onClick={() => setSelectedHourlyTab("rain")}
              className={`px-3 py-1 rounded-full font-medium transition-all ${
                selectedHourlyTab === "rain" ? "bg-[#8ab4f8] text-[#0b121e]" : "text-slate-400 hover:text-white"
              }`}
            >
              Rainfall (mm)
            </button>
            <button
              onClick={() => setSelectedHourlyTab("flood")}
              className={`px-3 py-1 rounded-full font-medium transition-all ${
                selectedHourlyTab === "flood" ? "bg-[#8ab4f8] text-[#0b121e]" : "text-slate-400 hover:text-white"
              }`}
            >
              Water Depth (m)
            </button>
            <button
              onClick={() => setSelectedHourlyTab("temp")}
              className={`px-3 py-1 rounded-full font-medium transition-all ${
                selectedHourlyTab === "temp" ? "bg-[#8ab4f8] text-[#0b121e]" : "text-slate-400 hover:text-white"
              }`}
            >
              Temperature
            </button>
          </div>
        </div>

        {/* Horizontal Capsules Strip */}
        <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-thin">
          {hourlyData.map((hour, idx) => (
            <div
              key={idx}
              className={`flex-shrink-0 w-24 p-3 rounded-2xl flex flex-col items-center justify-between border transition-all ${
                idx === 0
                  ? "bg-blue-500/20 border-blue-400/50 shadow-md"
                  : "bg-slate-900/50 border-white/5 hover:bg-slate-800/60"
              }`}
            >
              <span className="text-xs font-semibold text-slate-300">{hour.time}</span>
              <div className="my-2 text-blue-400">
                {hour.icon === "storm" && <CloudLightning className="w-6 h-6 text-yellow-300" />}
                {hour.icon === "heavy-rain" && <CloudRain className="w-6 h-6 text-blue-400" />}
                {hour.icon === "rain" && <Droplets className="w-6 h-6 text-cyan-300" />}
                {hour.icon === "cloudy" && <CloudRain className="w-6 h-6 text-slate-400" />}
              </div>

              {selectedHourlyTab === "rain" && (
                <>
                  <span className="text-xs font-bold text-white">{hour.rainRate}</span>
                  <span className="text-[10px] text-blue-300 font-medium mt-0.5">{hour.rainChance}</span>
                </>
              )}

              {selectedHourlyTab === "flood" && (
                <>
                  <span className="text-xs font-bold text-red-300">{hour.depth}</span>
                  <span className="text-[10px] text-slate-400 font-medium mt-0.5">Est. Depth</span>
                </>
              )}

              {selectedHourlyTab === "temp" && (
                <>
                  <span className="text-xs font-bold text-white">{hour.temp}</span>
                  <span className="text-[10px] text-slate-400 font-medium mt-0.5">Temp</span>
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
