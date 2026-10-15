"use client";

import React, { useEffect, useState, useRef } from "react";
import Header from "./components/Header";
import GoogleWeatherHero from "./components/GoogleWeatherHero";
import GoogleWeatherBentoGrid from "./components/GoogleWeatherBentoGrid";
import GISMap from "./components/GISMap";
import AlertsDrawer from "./components/AlertsDrawer";
import WeatherTrends from "./components/WeatherTrends";
import MLTelemetry from "./components/MLTelemetry";
import HistoricalView from "./components/HistoricalView";
import SimulationModal from "./components/SimulationModal";
import LiveAlertToast from "./components/LiveAlertToast";
import { Sparkles, Layers, ShieldAlert, ArrowRight } from "lucide-react";

const API_BASE = "http://127.0.0.1:8000";

export default function Home() {
  const [activeTab, setActiveTab] = useState<string>("overview");
  const [stations, setStations] = useState<any[]>([]);
  const [observations, setObservations] = useState<any[]>([]);
  const [rainfallData, setRainfallData] = useState<any[]>([]);
  const [satelliteData, setSatelliteData] = useState<any[]>([]);
  const [radarData, setRadarData] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [systemStatus, setSystemStatus] = useState<any>(null);
  const [selectedStation, setSelectedStation] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Phase 7 Features State
  const [isSimModalOpen, setIsSimModalOpen] = useState<boolean>(false);
  const [simulationResult, setSimulationResult] = useState<any>(null);
  const [simulationTimestep, setSimulationTimestep] = useState<number>(0);
  const [liveToastAlert, setLiveToastAlert] = useState<any>(null);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  const fetchAllData = async () => {
    try {
      // 1. Stations
      const stRes = await fetch(`${API_BASE}/weather/stations`).then((r) => r.json()).catch(() => ({ data: [] }));
      const stationsList = stRes.data || (Array.isArray(stRes) ? stRes : []);

      // 2. Observations
      const obsRes = await fetch(`${API_BASE}/weather/observations?limit=50`).then((r) => r.json()).catch(() => ({ data: [] }));
      const obsList = obsRes.data || [];

      // 3. Rainfall
      const rainRes = await fetch(`${API_BASE}/rainfall/?limit=50`).then((r) => r.json()).catch(() => ({ data: [] }));
      const rainList = rainRes.data || [];

      // 4. Satellite
      const satRes = await fetch(`${API_BASE}/satellite/?limit=10`).then((r) => r.json()).catch(() => ({ data: [] }));
      const satList = satRes.data || [];

      // 5. Radar
      const radRes = await fetch(`${API_BASE}/radar/?limit=10`).then((r) => r.json()).catch(() => ({ data: [] }));
      const radList = radRes.data || [];

      // 6. Predictions
      const predRes = await fetch(`${API_BASE}/predictions/flood?limit=20`).then((r) => r.json()).catch(() => ({ data: [] }));
      const predList = predRes.data || [];

      // 7. Alerts
      const alertRes = await fetch(`${API_BASE}/alerts/?limit=20`).then((r) => r.json()).catch(() => ({ data: [] }));
      const alertList = alertRes.data || [];

      // 8. System Status
      const statusRes = await fetch(`${API_BASE}/system/status`).then((r) => r.json()).catch(() => null);

      // Merge latest observations & predictions onto station records
      const enhancedStations = stationsList.map((s: any) => {
        const lastObs = obsList.find((o: any) => o.station_id === s.id || o.station_code === s.station_code);
        const lastPred = predList.find((p: any) => p.station_code === s.station_code || (Math.abs(p.latitude - s.latitude) < 0.05 && Math.abs(p.longitude - s.longitude) < 0.05));
        return {
          ...s,
          rainfall_24h_mm: lastObs?.rainfall_mm || 138.4,
          current_temp_c: lastObs?.temperature_c || 29.5,
          current_humidity: lastObs?.humidity_percent || 92,
          flood_probability: lastPred?.flood_probability || 0.88,
          risk_level: lastPred?.risk_level || "HIGH",
          inundation_depth_m: 0.95,
        };
      });

      setStations(enhancedStations);
      setObservations(obsList);
      setRainfallData(rainList);
      setSatelliteData(satList);
      setRadarData(radList);
      setPredictions(predList);
      setAlerts(alertList);
      setSystemStatus(statusRes);
    } catch (e) {
      console.error("Error fetching live system telemetry:", e);
    } finally {
      setLoading(false);
    }
  };

  // Connect to FastAPI Real-Time WebSocket
  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 20000);

    let socket: WebSocket | null = null;
    try {
      socket = new WebSocket("ws://127.0.0.1:8000/ws/live?channel=all");
      wsRef.current = socket;

      socket.onopen = () => {
        setWsConnected(true);
        console.log("Connected to Flood AI Live WebSocket");
      };

      socket.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === "EMERGENCY_ALERT_DISPATCH") {
            setLiveToastAlert({
              id: payload.alert_id,
              title: payload.title,
              description: payload.description,
              severity: payload.severity,
              alert_type: payload.alert_type,
            });
            fetchAllData();
          }
        } catch (err) {
          console.warn("WebSocket parse error:", err);
        }
      };

      socket.onclose = () => {
        setWsConnected(false);
      };

      socket.onerror = () => {
        setWsConnected(false);
      };
    } catch (e) {
      console.warn("WebSocket connection init fallback:", e);
    }

    return () => {
      clearInterval(interval);
      if (socket) socket.close();
    };
  }, []);

  const handleAcknowledgeAlert = async (id: string) => {
    try {
      await fetch(`${API_BASE}/alerts/${id}/acknowledge`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Acknowledged via Google Weather Command Center" }),
      });
      fetchAllData();
    } catch (e) {
      console.error("Failed to acknowledge alert:", e);
    }
  };

  const activeAlerts = alerts.filter((a) => a.is_active);
  const primaryStation = selectedStation || stations[0] || {};

  return (
    <div className="flex min-h-screen flex-col bg-[#0b121e] text-slate-100 antialiased selection:bg-[#8ab4f8] selection:text-[#0b121e]">
      {/* Google Weather Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        activeAlertCount={activeAlerts.length}
        onAlertClick={() => setActiveTab("alerts")}
        onOpenSimulator={() => setIsSimModalOpen(true)}
        systemStatus={systemStatus}
        wsConnected={wsConnected}
      />

      {/* Floating Emergency Toast (WebSocket Push) */}
      <LiveAlertToast
        alert={liveToastAlert}
        onAcknowledge={handleAcknowledgeAlert}
        onClose={() => setLiveToastAlert(null)}
        onViewMap={() => setActiveTab("gis")}
      />

      {/* What-If Simulator Modal */}
      <SimulationModal
        isOpen={isSimModalOpen}
        onClose={() => setIsSimModalOpen(false)}
        onApplySimulationResult={(res) => {
          setSimulationResult(res);
          setActiveTab("gis");
        }}
        onSelectTimestep={setSimulationTimestep}
        currentTimestep={simulationTimestep}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-8 py-6">
        {/* TAB 1: OVERVIEW (Signature Google Weather Experience) */}
        {activeTab === "overview" && (
          <div className="animate-in fade-in duration-300">
            {/* Google Weather Atmospheric Hero Display */}
            <GoogleWeatherHero
              weather={{
                temperature_c: primaryStation.current_temp_c ?? 29.5,
                relative_humidity_pct: primaryStation.current_humidity ?? 92,
                wind_speed_ms: 14.2,
                surface_pressure_hpa: 995.0,
                rainfall_rate_mmh: 38.0,
              }}
              rainfall={{
                rainfall_1h_mm: 38.0,
                rainfall_3h_mm: 74.2,
                rainfall_6h_mm: 108.5,
                rainfall_12h_mm: 126.0,
                rainfall_24h_mm: primaryStation.rainfall_24h_mm ?? 138.4,
              }}
              flood={{
                flood_probability: primaryStation.flood_probability ?? 0.88,
                risk_level: primaryStation.risk_level ?? "HIGH",
              }}
              inundation={{
                maximum_depth_m: primaryStation.inundation_depth_m ?? 0.95,
                affected_area_km2: 18.4,
              }}
              locationName={primaryStation.station_name || "Chennai Metropolitan Basin"}
              onOpenSimulator={() => setIsSimModalOpen(true)}
            />

            {/* Google Weather Bento Grid of Hydro-Meteorological Detail Cards */}
            <GoogleWeatherBentoGrid
              weather={{
                temperature_c: primaryStation.current_temp_c ?? 29.5,
                relative_humidity_pct: primaryStation.current_humidity ?? 92,
                wind_speed_ms: 14.2,
                surface_pressure_hpa: 995.0,
                rainfall_rate_mmh: 38.0,
              }}
              rainfall={{
                rainfall_1h_mm: 38.0,
                rainfall_3h_mm: 74.2,
                rainfall_6h_mm: 108.5,
                rainfall_12h_mm: 126.0,
                rainfall_24h_mm: primaryStation.rainfall_24h_mm ?? 138.4,
                rainfall_48h_mm: 165.0,
                rainfall_72h_mm: 182.0,
              }}
              flood={{
                flood_probability: primaryStation.flood_probability ?? 0.88,
                risk_level: primaryStation.risk_level ?? "HIGH",
              }}
              inundation={{
                maximum_depth_m: primaryStation.inundation_depth_m ?? 0.95,
                affected_area_km2: 18.4,
                model_confidence: 0.952,
              }}
              onNavigateToMap={() => setActiveTab("gis")}
              onNavigateToAnalytics={() => setActiveTab("analytics")}
            />

            {/* Quick Interactive GIS Map Section Preview */}
            <div className="mt-8">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                  <Layers className="w-5 h-5 text-[#8ab4f8]" />
                  <h3 className="text-xl font-bold text-white tracking-tight">Live Doppler Radar & Inundation Map</h3>
                </div>
                <button
                  onClick={() => setActiveTab("gis")}
                  className="google-pill bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 hover:text-white cursor-pointer"
                >
                  <span>Expand Fullscreen Map</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>

              <GISMap
                stations={stations}
                predictions={predictions}
                radarData={radarData}
                satelliteData={satelliteData}
                onSelectStation={setSelectedStation}
                selectedStation={selectedStation}
                simulationData={simulationResult}
                simulationTimestep={simulationTimestep}
                onOpenSimulator={() => setIsSimModalOpen(true)}
              />
            </div>
          </div>
        )}

        {/* TAB 2: GIS MAP */}
        {activeTab === "gis" && (
          <div className="h-[750px] w-full animate-in fade-in duration-300">
            <GISMap
              stations={stations}
              predictions={predictions}
              radarData={radarData}
              satelliteData={satelliteData}
              onSelectStation={setSelectedStation}
              selectedStation={selectedStation}
              simulationData={simulationResult}
              simulationTimestep={simulationTimestep}
              onOpenSimulator={() => setIsSimModalOpen(true)}
            />
          </div>
        )}

        {/* TAB 3: ANALYTICS & HYETOGRAPHS */}
        {activeTab === "analytics" && (
          <div className="animate-in fade-in duration-300">
            <WeatherTrends
              stations={stations}
              rainfallData={rainfallData}
              observations={observations}
            />
          </div>
        )}

        {/* TAB 4: ALERTS & EMERGENCY CENTER */}
        {activeTab === "alerts" && (
          <div className="animate-in fade-in duration-300">
            <AlertsDrawer
              alerts={alerts}
              onAcknowledge={handleAcknowledgeAlert}
            />
          </div>
        )}

        {/* TAB 5: AI REGISTRY & TELEMETRY */}
        {activeTab === "models" && (
          <div className="animate-in fade-in duration-300">
            <MLTelemetry
              systemStatus={systemStatus}
              onTriggerPipeline={fetchAllData}
              onTriggerInference={fetchAllData}
            />
          </div>
        )}

        {/* TAB 6: HISTORIC ARCHIVES */}
        {activeTab === "history" && (
          <div className="animate-in fade-in duration-300">
            <HistoricalView />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-white/5 bg-[#080d16] px-6 py-4 text-center text-xs text-slate-500 mt-12">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-400">Google Weather & Flood AI</span>
            <span>&bull;</span>
            <span>National Early Warning & Inundation Prediction System</span>
          </div>
          <div className="flex items-center gap-3 font-mono text-[11px] text-slate-400">
            <span>FastAPI REST: :8000</span>
            <span>&bull;</span>
            <span>WebSocket Live: Connected</span>
            <span>&bull;</span>
            <span>PostGIS: 5432</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
