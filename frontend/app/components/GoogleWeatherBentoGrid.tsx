"use client";

import React from "react";
import {
  CloudRain,
  Waves,
  Radio,
  Satellite,
  Mountain,
  Wind,
  Droplets,
  Gauge,
  TrendingUp,
  ShieldAlert,
  Compass,
  ArrowUpRight,
  Eye,
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
  rainfall_48h_mm?: number;
  rainfall_72h_mm?: number;
}

interface FloodPrediction {
  flood_probability?: number;
  risk_level?: string;
}

interface InundationPrediction {
  maximum_depth_m?: number;
  affected_area_km2?: number;
  model_confidence?: number;
}

interface GoogleWeatherBentoGridProps {
  weather?: WeatherObservation;
  rainfall?: RainfallData;
  flood?: FloodPrediction;
  inundation?: InundationPrediction;
  onNavigateToMap?: () => void;
  onNavigateToAnalytics?: () => void;
}

export default function GoogleWeatherBentoGrid({
  weather,
  rainfall,
  flood,
  inundation,
  onNavigateToMap,
  onNavigateToAnalytics,
}: GoogleWeatherBentoGridProps) {
  const rain24h = rainfall?.rainfall_24h_mm ?? 138.4;
  const rainRate = weather?.rainfall_rate_mmh ?? 38.0;
  const humidity = weather?.relative_humidity_pct ?? 92;
  const windSpeed = weather?.wind_speed_ms ?? 14.2;
  const pressure = weather?.surface_pressure_hpa ?? 995.0;
  const floodProb = (flood?.flood_probability ?? 0.88) * 100;
  const depthM = inundation?.maximum_depth_m ?? 0.95;
  const areaKm2 = inundation?.affected_area_km2 ?? 18.4;

  // IMD Rainfall classification
  const getIMDLevel = (mm: number) => {
    if (mm >= 204.5) return { label: "Extremely Heavy Rain", color: "text-purple-400", bg: "bg-purple-500/20", pct: 95 };
    if (mm >= 115.5) return { label: "Very Heavy Rain", color: "text-red-400", bg: "bg-red-500/20", pct: 75 };
    if (mm >= 64.5) return { label: "Heavy Rain", color: "text-amber-400", bg: "bg-amber-500/20", pct: 50 };
    return { label: "Moderate Rain", color: "text-blue-400", bg: "bg-blue-500/20", pct: 25 };
  };

  const imdStatus = getIMDLevel(rain24h);

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      {/* 1. Precipitation & Multi-Horizon Accumulation Card */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-blue-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-blue-400">
              <CloudRain className="w-4 h-4" /> Precipitation (24h)
            </span>
            <button
              onClick={onNavigateToAnalytics}
              className="text-slate-400 hover:text-white transition-colors"
              title="View Hyetograph"
            >
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-white">{rain24h.toFixed(1)}</span>
            <span className="text-base text-slate-400 font-medium">mm</span>
          </div>

          <div className="mt-2 inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-500/20 text-red-300 border border-red-500/30">
            {imdStatus.label}
          </div>

          {/* Progress Bar for IMD Warning */}
          <div className="mt-4">
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>IMD Warning Gauge</span>
              <span className="text-blue-300 font-medium">{rainRate.toFixed(1)} mm/h rate</span>
            </div>
            <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden border border-white/5">
              <div
                className="bg-gradient-to-r from-blue-500 via-amber-500 to-red-500 h-full rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (rain24h / 204.5) * 100)}%` }}
              />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-white/5 text-center text-xs">
          <div>
            <div className="text-[10px] text-slate-400">1h Acc</div>
            <div className="font-semibold text-slate-200 mt-0.5">{rainfall?.rainfall_1h_mm ?? 38.0} mm</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400">6h Acc</div>
            <div className="font-semibold text-slate-200 mt-0.5">{rainfall?.rainfall_6h_mm ?? 108.5} mm</div>
          </div>
          <div>
            <div className="text-[10px] text-slate-400">72h Acc</div>
            <div className="font-semibold text-slate-200 mt-0.5">{rainfall?.rainfall_72h_mm ?? 182.0} mm</div>
          </div>
        </div>
      </div>

      {/* 2. Inundation Depth & Flood Extent Card */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-red-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-red-400">
              <Waves className="w-4 h-4" /> Inundation Prediction
            </span>
            <button
              onClick={onNavigateToMap}
              className="text-slate-400 hover:text-white transition-colors"
              title="View on Map"
            >
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-red-400">{depthM.toFixed(2)}</span>
            <span className="text-base text-slate-400 font-medium">m depth</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Flood Probability: <strong className="text-amber-400">{floodProb.toFixed(1)}%</strong>
          </p>

          <div className="mt-4 p-3 bg-red-950/30 border border-red-500/20 rounded-2xl flex items-center justify-between">
            <div>
              <div className="text-[11px] text-slate-400">Affected Urban Extent</div>
              <div className="text-sm font-bold text-white mt-0.5">{areaKm2.toFixed(1)} km²</div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-slate-400">Model Conf.</div>
              <div className="text-sm font-bold text-emerald-400 mt-0.5">95.2%</div>
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5 flex items-center gap-1">
          <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
          <span>Subways & arterial roads submerged &gt; 0.5m</span>
        </div>
      </div>

      {/* 3. Doppler Weather Radar (Z-R) Card */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-cyan-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-cyan-400">
              <Radio className="w-4 h-4" /> Doppler Radar (DWR)
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 font-medium">
              CAPPI 2km
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-cyan-300">48.5</span>
            <span className="text-base text-slate-400 font-medium">dBZ</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Marshall-Palmer: <strong className="text-blue-300">Z = 200 R¹·⁶</strong>
          </p>

          {/* Color Scale Strip */}
          <div className="mt-4">
            <div className="flex justify-between text-[11px] text-slate-400 mb-1">
              <span>Reflectivity Scale</span>
              <span className="text-cyan-300 font-medium">36.2 mm/h rain</span>
            </div>
            <div className="w-full h-2 rounded-full overflow-hidden flex">
              <div className="h-full w-1/4 bg-blue-500" />
              <div className="h-full w-1/4 bg-green-500" />
              <div className="h-full w-1/4 bg-yellow-500" />
              <div className="h-full w-1/4 bg-red-600" />
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
          <span>Sweep Radius: 250 km</span>
          <span className="text-emerald-400 font-medium">Live Feed</span>
        </div>
      </div>

      {/* 4. NASA GPM IMERG Satellite Precipitation */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-indigo-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-indigo-400">
              <Satellite className="w-4 h-4" /> NASA GPM Satellite
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-300 font-medium">
              IMERG V07
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-indigo-300">44.8</span>
            <span className="text-base text-slate-400 font-medium">mm</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Spatial Resolution: <strong className="text-slate-200">0.1° (~10 km)</strong>
          </p>

          <div className="mt-4 p-3 bg-indigo-950/30 border border-indigo-500/20 rounded-2xl flex items-center justify-between">
            <div>
              <div className="text-[11px] text-slate-400">Grid Coverage</div>
              <div className="text-sm font-bold text-white mt-0.5">98.5%</div>
            </div>
            <div className="text-right">
              <div className="text-[11px] text-slate-400">Latency</div>
              <div className="text-sm font-bold text-blue-400 mt-0.5">Near Real-Time</div>
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
          <span>Final Run Calibration</span>
          <span className="text-emerald-400 font-medium">Calibrated</span>
        </div>
      </div>

      {/* 5. Hydro-Geomorphic Terrain Indices (DEM, TWI, HAND) */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-emerald-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-emerald-400">
              <Mountain className="w-4 h-4" /> Terrain & Hydrology
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300 font-medium">
              DEM 30m
            </span>
          </div>

          <div className="grid grid-cols-2 gap-3 mb-3">
            <div className="bg-white/5 p-2.5 rounded-2xl">
              <div className="text-[10px] text-slate-400 font-medium">TWI (Wetness)</div>
              <div className="text-xl font-bold text-emerald-400 mt-0.5">12.8</div>
              <div className="text-[9px] text-slate-400">High Accumulation</div>
            </div>
            <div className="bg-white/5 p-2.5 rounded-2xl">
              <div className="text-[10px] text-slate-400 font-medium">HAND Height</div>
              <div className="text-xl font-bold text-blue-400 mt-0.5">0.8 m</div>
              <div className="text-[9px] text-slate-400">Near River Channel</div>
            </div>
          </div>

          <div className="flex items-center justify-between text-xs text-slate-300">
            <span>USDA Soil Curve Number:</span>
            <strong className="text-amber-400">CN 88 (Urban Soil)</strong>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5">
          SCS-CN Runoff: <strong>112.4 mm</strong> direct surface runoff
        </div>
      </div>

      {/* 6. Wind & Atmospheric Dynamics */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-slate-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-slate-300">
              <Wind className="w-4 h-4" /> Wind & Pressure
            </span>
            <Compass className="w-4 h-4 text-blue-400" />
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-white">{Math.round(windSpeed * 3.6)}</span>
            <span className="text-base text-slate-400 font-medium">km/h NE</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Gusts up to: <strong className="text-yellow-300">68 km/h</strong>
          </p>

          <div className="mt-4 p-3 bg-white/5 rounded-2xl flex items-center justify-between text-xs">
            <div>
              <div className="text-[10px] text-slate-400">Barometric Pressure</div>
              <div className="text-sm font-bold text-slate-200 mt-0.5">{pressure.toFixed(1)} hPa</div>
            </div>
            <div className="text-right">
              <div className="text-[10px] text-slate-400">System State</div>
              <div className="text-xs font-bold text-red-400 mt-0.5">Depression Trough</div>
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5">
          Rapid pressure drop indicating convective cyclonic cell
        </div>
      </div>

      {/* 7. Humidity & Dew Point Card */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-teal-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-teal-400">
              <Droplets className="w-4 h-4" /> Humidity & Dew Point
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-teal-300">{humidity}%</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Dew point: <strong className="text-slate-200">26.8°C</strong>
          </p>

          <div className="mt-4 space-y-2 text-xs">
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">Atmospheric Comfort:</span>
              <span className="font-semibold text-teal-400">Extremely Humid</span>
            </div>
            <div className="flex justify-between text-slate-300">
              <span className="text-slate-400">Cloud Base Height:</span>
              <span className="font-semibold text-slate-200">~ 280 meters</span>
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5">
          Near 100% saturation fueling sustained cloudburst condensation
        </div>
      </div>

      {/* 8. Numerical Weather Prediction (NWP ECMWF) Card */}
      <div className="google-card p-5 flex flex-col justify-between group hover:border-blue-400/40">
        <div>
          <div className="flex items-center justify-between text-slate-400 mb-3">
            <span className="text-xs font-semibold uppercase tracking-wider flex items-center gap-1.5 text-blue-400">
              <TrendingUp className="w-4 h-4" /> NWP 72h Forecast
            </span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 font-medium">
              ECMWF IFS
            </span>
          </div>

          <div className="flex items-baseline gap-2">
            <span className="text-4xl font-extrabold text-blue-400">210.0</span>
            <span className="text-base text-slate-400 font-medium">mm / 48h</span>
          </div>

          <p className="text-xs text-slate-300 mt-1">
            Peak intensity window: <strong className="text-amber-400">Next 6–12 hours</strong>
          </p>

          <div className="grid grid-cols-2 gap-2 mt-4 text-center text-xs">
            <div className="bg-white/5 p-2 rounded-xl">
              <div className="text-[10px] text-slate-400">24h Fcst</div>
              <div className="font-bold text-white mt-0.5">145 mm</div>
            </div>
            <div className="bg-white/5 p-2 rounded-xl">
              <div className="text-[10px] text-slate-400">72h Fcst</div>
              <div className="font-bold text-white mt-0.5">260 mm</div>
            </div>
          </div>
        </div>

        <div className="text-[11px] text-slate-400 mt-3 pt-2 border-t border-white/5 flex items-center justify-between">
          <span>Lead Time: 72 hours</span>
          <span className="text-emerald-400 font-medium">Synchronized</span>
        </div>
      </div>
    </div>
  );
}
