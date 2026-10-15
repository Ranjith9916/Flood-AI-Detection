"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Layers,
  MapPin,
  Radio,
  Satellite,
  Waves,
  Eye,
  EyeOff,
  Navigation,
  Info,
  Droplets,
  Wind,
  Compass,
  Sparkles,
  Maximize2,
} from "lucide-react";

interface Station {
  id: string;
  station_code: string;
  station_name: string;
  latitude: number;
  longitude: number;
  elevation_m?: number;
  source: string;
  current_temp_c?: number;
  current_humidity?: number;
  rainfall_24h_mm?: number;
  flood_probability?: number;
  inundation_depth_m?: number;
  risk_level?: string;
}

interface GISMapProps {
  stations: Station[];
  predictions: any[];
  radarData: any[];
  satelliteData: any[];
  onSelectStation: (station: Station) => void;
  selectedStation: Station | null;
  simulationData?: any;
  simulationTimestep?: number;
  onOpenSimulator?: () => void;
}

export default function GISMap({
  stations,
  predictions,
  radarData,
  satelliteData,
  onSelectStation,
  selectedStation,
  simulationData,
  simulationTimestep = 0,
  onOpenSimulator,
}: GISMapProps) {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<any>(null);
  const leafletRef = useRef<any>(null);
  const layersRef = useRef<{ [key: string]: any }>({});

  const [visibleLayers, setVisibleLayers] = useState<{ [key: string]: boolean }>({
    stations: true,
    inundation: true,
    radar: true,
    satellite: true,
    drainage: true,
    simulation: true,
  });

  const [activeLegend, setActiveLegend] = useState<string>("inundation");

  const toggleLayer = (layerKey: string) => {
    setVisibleLayers((prev) => {
      const next = { ...prev, [layerKey]: !prev[layerKey] };
      const layerGroup = layersRef.current[layerKey];
      if (layerGroup && mapInstanceRef.current) {
        if (next[layerKey]) {
          mapInstanceRef.current.addLayer(layerGroup);
        } else {
          mapInstanceRef.current.removeLayer(layerGroup);
        }
      }
      return next;
    });
  };

  // 1. Initialize Map Once on Mount
  useEffect(() => {
    if (typeof window === "undefined" || !mapContainerRef.current) return;

    let isMounted = true;

    import("leaflet").then((L) => {
      if (!isMounted || !mapContainerRef.current || mapInstanceRef.current) return;

      leafletRef.current = L;

      const map = L.map(mapContainerRef.current, {
        center: [13.0827, 80.2707],
        zoom: 11,
        zoomControl: false,
      });

      L.control.zoom({ position: "bottomright" }).addTo(map);

      // Dark Carto Base Tiles
      L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: '&copy; <a href="https://carto.com/">CARTO</a> &bull; Flood AI',
        maxZoom: 19,
        subdomains: "abcd",
      }).addTo(map);

      // Layer Groups
      const stationGroup = L.layerGroup().addTo(map);
      const inundationGroup = L.layerGroup().addTo(map);
      const radarGroup = L.layerGroup().addTo(map);
      const satelliteGroup = L.layerGroup().addTo(map);
      const drainageGroup = L.layerGroup().addTo(map);
      const simulationGroup = L.layerGroup().addTo(map);

      layersRef.current = {
        stations: stationGroup,
        inundation: inundationGroup,
        radar: radarGroup,
        satellite: satelliteGroup,
        drainage: drainageGroup,
        simulation: simulationGroup,
      };

      // Draw River & Drainage Channels (Chennai Coastal Basin & Adyar/Cooum)
      const riverChannels = [
        {
          name: "Adyar River Basin & Outfall",
          coords: [
            [12.985, 80.12],
            [13.005, 80.18],
            [13.012, 80.24],
            [13.013, 80.275],
          ],
          color: "#06b6d4",
        },
        {
          name: "Cooum River Urban Drainage Axis",
          coords: [
            [13.075, 80.15],
            [13.078, 80.21],
            [13.072, 80.26],
            [13.068, 80.285],
          ],
          color: "#3b82f6",
        },
        {
          name: "Buckingham Canal North-South Axis",
          coords: [
            [13.15, 80.29],
            [13.08, 80.28],
            [13.01, 80.26],
            [12.92, 80.24],
          ],
          color: "#6366f1",
        },
      ];

      riverChannels.forEach((v) => {
        const polyline = L.polyline(v.coords as any, {
          color: v.color,
          weight: 4,
          opacity: 0.85,
          dashArray: "6, 8",
        }).bindTooltip(`<b>${v.name}</b><br>Primary Stormwater Flow Channel`, {
          sticky: true,
        });
        drainageGroup.addLayer(polyline);
      });

      // Draw Baseline Inundation Contours
      const floodDepths = [
        { lat: 13.012, lon: 80.245, depth: 1.45, risk: "CRITICAL", area: "Adyar Saidapet Bridge Basin" },
        { lat: 13.072, lon: 80.258, depth: 0.95, risk: "HIGH", area: "Central Railway Corridor Subway" },
        { lat: 12.965, lon: 80.215, depth: 1.20, risk: "CRITICAL", area: "Velachery Lake Depression" },
        { lat: 13.085, lon: 80.285, depth: 0.65, risk: "MODERATE", area: "North Marina Coastal Drain" },
        { lat: 13.035, lon: 80.165, depth: 0.85, risk: "HIGH", area: "Porur Lake Overflow Axis" },
      ];

      floodDepths.forEach((pt) => {
        const color = pt.depth > 1.0 ? "#ef4444" : pt.depth > 0.5 ? "#ea580c" : "#f59e0b";
        const radius = pt.depth * 950 + 400;

        const circle = L.circle([pt.lat, pt.lon], {
          radius: radius,
          fillColor: color,
          fillOpacity: 0.35,
          color: color,
          weight: 2,
        }).bindPopup(`
          <div class="p-2 space-y-1.5 text-xs">
            <div class="font-bold text-sm text-slate-100">${pt.area}</div>
            <div class="flex items-center justify-between border-t border-slate-700 pt-1">
              <span class="text-slate-400">Est. Water Depth:</span>
              <span class="font-bold text-cyan-400 text-sm">${pt.depth.toFixed(2)} m</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-slate-400">Risk Severity:</span>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${
                pt.risk === "CRITICAL" ? "bg-red-500/20 text-red-400" : "bg-amber-500/20 text-amber-400"
              }">${pt.risk}</span>
            </div>
          </div>
        `);
        inundationGroup.addLayer(circle);
      });

      // Draw Doppler Radar Sweeps
      const radarCenters = [
        { lat: 13.0827, lon: 80.2707, dbz: 48.5, rain_rate: 36.2 },
        { lat: 12.98, lon: 80.18, dbz: 42.0, rain_rate: 22.5 },
        { lat: 13.15, lon: 80.22, dbz: 34.0, rain_rate: 9.8 },
      ];

      radarCenters.forEach((r) => {
        const radCircle = L.circle([r.lat, r.lon], {
          radius: 5200,
          fillColor: r.dbz > 45 ? "#ef4444" : r.dbz > 35 ? "#f59e0b" : "#10b981",
          fillOpacity: 0.22,
          color: r.dbz > 45 ? "#f87171" : "#34d399",
          weight: 1.5,
          dashArray: "4, 6",
        }).bindTooltip(`<b>DWR Doppler Scan</b><br>Reflectivity: ${r.dbz} dBZ<br>Rain Rate: ${r.rain_rate} mm/h`, {
          sticky: true,
        });
        radarGroup.addLayer(radCircle);
      });

      mapInstanceRef.current = map;
    });

    return () => {
      isMounted = false;
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, []);

  // 2. Dynamic Station Markers
  useEffect(() => {
    const L = leafletRef.current;
    const stationGroup = layersRef.current["stations"];
    if (!L || !stationGroup) return;

    stationGroup.clearLayers();

    stations.forEach((st) => {
      const isCritical = (st.rainfall_24h_mm || 0) > 64.5 || (st.flood_probability || 0) > 0.5;

      const customIcon = L.divIcon({
        className: "custom-station-pin",
        html: `
          <div class="relative flex items-center justify-center cursor-pointer group">
            <div class="h-9 w-9 rounded-full flex items-center justify-center ${
              isCritical
                ? "bg-red-500 text-white shadow-lg shadow-red-500/50 pulse-alert"
                : "bg-[#8ab4f8] text-[#0b121e] shadow-lg shadow-blue-500/40"
            } border-2 border-white transition-transform group-hover:scale-115">
              <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div class="absolute -bottom-6 whitespace-nowrap px-2 py-0.5 rounded-full bg-[#111c30]/95 border border-white/10 text-[10px] font-bold text-slate-200 shadow-md">
              ${st.station_code}
            </div>
          </div>
        `,
        iconSize: [36, 36],
        iconAnchor: [18, 18],
      });

      const marker = L.marker([st.latitude, st.longitude], { icon: customIcon });

      marker.on("click", () => {
        onSelectStation(st);
      });

      marker.bindPopup(`
        <div class="p-3 space-y-2 text-xs min-w-[220px]">
          <div class="flex items-center justify-between border-b border-white/10 pb-2">
            <div>
              <div class="font-bold text-sm text-white">${st.station_name || st.station_code}</div>
              <div class="text-[10px] text-slate-400 font-mono">${st.latitude.toFixed(4)}°N, ${st.longitude.toFixed(4)}°E</div>
            </div>
            <span class="rounded-full bg-blue-500/20 px-2 py-0.5 text-[9px] font-bold text-blue-300 border border-blue-500/30">
              ${st.source}
            </span>
          </div>

          <div class="grid grid-cols-2 gap-2 text-[11px] pt-1">
            <div class="rounded-2xl bg-white/5 p-2 border border-white/5">
              <div class="text-[10px] text-slate-400">24h Rain</div>
              <div class="font-bold text-blue-400 text-sm mt-0.5">${(st.rainfall_24h_mm || 0).toFixed(1)} mm</div>
            </div>
            <div class="rounded-2xl bg-white/5 p-2 border border-white/5">
              <div class="text-[10px] text-slate-400">Flood Prob</div>
              <div class="font-bold text-emerald-400 text-sm mt-0.5">${((st.flood_probability || 0.001) * 100).toFixed(1)}%</div>
            </div>
          </div>
        </div>
      `);

      stationGroup.addLayer(marker);
    });
  }, [stations]);

  // 3. Dynamic Simulation Contours Render
  useEffect(() => {
    const L = leafletRef.current;
    const simGroup = layersRef.current["simulation"];
    if (!L || !simGroup) return;

    simGroup.clearLayers();

    if (simulationData && simulationData.timeline) {
      const step = simulationData.timeline.find((t: any) => t.timestep_hours === simulationTimestep) || simulationData.timeline[0];
      if (step && step.geojson_features) {
        step.geojson_features.forEach((feat: any) => {
          const coords = feat.geometry.coordinates[0].map((c: any) => [c[1], c[0]]);
          const polygon = L.polygon(coords, {
            color: feat.properties.color,
            fillColor: feat.properties.fillColor,
            fillOpacity: feat.properties.fillOpacity,
            weight: 2,
          }).bindPopup(`
            <div class="p-2 text-xs">
              <div class="font-bold text-white">${feat.properties.zone}</div>
              <div class="text-blue-300">Water Depth: ${feat.properties.depth_m} m</div>
              <div class="text-slate-400 text-[10px] mt-1">Timestep: T+${simulationTimestep} Hours</div>
            </div>
          `);
          simGroup.addLayer(polygon);
        });
      }
    }
  }, [simulationData, simulationTimestep]);

  return (
    <div className="relative h-[650px] w-full overflow-hidden rounded-3xl google-card border border-white/10 shadow-2xl">
      {/* Map Canvas */}
      <div ref={mapContainerRef} className="h-full w-full" />

      {/* Floating Layer Control Pills (Google Style) */}
      <div className="absolute top-4 left-4 z-[400] flex flex-col gap-2 rounded-2xl bg-[#111c30]/90 p-3.5 shadow-2xl backdrop-blur-xl border border-white/10 max-w-xs">
        <div className="flex items-center justify-between border-b border-white/10 pb-2">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#8ab4f8]">
            <Layers className="h-4 w-4" />
            <span>Map Layers</span>
          </div>
          {onOpenSimulator && (
            <button
              onClick={onOpenSimulator}
              className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 hover:bg-blue-500/30 border border-blue-500/30 flex items-center gap-1 cursor-pointer"
            >
              <Sparkles className="w-3 h-3 text-yellow-300" />
              Simulate
            </button>
          )}
        </div>

        <div className="space-y-1.5 text-xs">
          {[
            { key: "stations", label: "AWS Weather Stations", icon: MapPin, color: "text-[#8ab4f8]" },
            { key: "inundation", label: "AI Inundation Contours", icon: Waves, color: "text-red-400" },
            { key: "radar", label: "Doppler Radar (dBZ)", icon: Radio, color: "text-cyan-400" },
            { key: "drainage", label: "River & Catchment Channels", icon: Navigation, color: "text-blue-400" },
            { key: "satellite", label: "NASA GPM Satellite", icon: Satellite, color: "text-indigo-400" },
          ].map((item) => {
            const Icon = item.icon;
            const isVisible = visibleLayers[item.key];
            return (
              <button
                key={item.key}
                type="button"
                onClick={() => toggleLayer(item.key)}
                className={`flex w-full items-center justify-between gap-3 rounded-xl px-2.5 py-1.5 cursor-pointer transition-all ${
                  isVisible ? "bg-white/10 text-white font-medium" : "text-slate-500 hover:bg-white/5"
                }`}
              >
                <div className="flex items-center gap-2">
                  <Icon className={`h-3.5 w-3.5 ${isVisible ? item.color : "text-slate-600"}`} />
                  <span className="text-xs">{item.label}</span>
                </div>
                {isVisible ? <Eye className="h-3.5 w-3.5 text-[#8ab4f8]" /> : <EyeOff className="h-3.5 w-3.5 text-slate-600" />}
              </button>
            );
          })}
        </div>
      </div>

      {/* Floating Legend (Google Style) */}
      <div className="absolute bottom-4 left-4 z-[400] rounded-2xl bg-[#111c30]/90 p-3 shadow-xl backdrop-blur-xl border border-white/10">
        <div className="flex items-center justify-between gap-4 border-b border-white/10 pb-1.5 text-xs font-semibold text-slate-300">
          <div className="flex items-center gap-1.5">
            <Info className="h-3.5 w-3.5 text-[#8ab4f8]" />
            <span>Map Severity Scale</span>
          </div>
        </div>

        <div className="mt-2 flex items-center gap-3 text-[11px]">
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-amber-400"></span>
            <span className="text-slate-300">Minor (&lt;0.3m)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-orange-500"></span>
            <span className="text-slate-300">Moderate (0.3–1.0m)</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-red-500"></span>
            <span className="text-slate-300">Critical (&gt;1.0m)</span>
          </div>
        </div>
      </div>

      {/* Selected Station Telemetry HUD Card (Google Weather Style) */}
      {selectedStation && (
        <div className="absolute top-4 right-4 z-[400] w-80 rounded-3xl bg-[#111c30]/95 p-5 shadow-2xl backdrop-blur-2xl border border-white/15">
          <div className="flex items-start justify-between border-b border-white/10 pb-3">
            <div>
              <div className="text-[10px] font-bold uppercase tracking-wider text-[#8ab4f8]">AWS Station Telemetry</div>
              <h3 className="text-base font-bold text-white mt-0.5">{selectedStation.station_name || selectedStation.station_code}</h3>
              <p className="text-xs text-slate-400 font-mono">
                {selectedStation.latitude.toFixed(4)}°N, {selectedStation.longitude.toFixed(4)}°E
              </p>
            </div>
            <button
              type="button"
              onClick={() => onSelectStation(null as any)}
              className="w-7 h-7 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center text-slate-400 hover:text-white text-xs cursor-pointer"
            >
              ✕
            </button>
          </div>

          <div className="mt-3 grid grid-cols-2 gap-2.5 text-xs">
            <div className="rounded-2xl bg-white/5 p-2.5 border border-white/5">
              <div className="flex items-center gap-1 text-slate-400 text-[11px]">
                <Droplets className="h-3.5 w-3.5 text-cyan-400" />
                <span>24h Rainfall</span>
              </div>
              <div className="mt-1 text-lg font-extrabold text-white">{(selectedStation.rainfall_24h_mm || 0).toFixed(1)} <span className="text-xs text-slate-400 font-normal">mm</span></div>
            </div>

            <div className="rounded-2xl bg-white/5 p-2.5 border border-white/5">
              <div className="flex items-center gap-1 text-slate-400 text-[11px]">
                <Waves className="h-3.5 w-3.5 text-amber-400" />
                <span>Flood Risk</span>
              </div>
              <div className="mt-1 text-lg font-extrabold text-emerald-400">
                {((selectedStation.flood_probability || 0.001) * 100).toFixed(1)}%
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
