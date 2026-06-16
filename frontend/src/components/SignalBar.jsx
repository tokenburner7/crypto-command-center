import { useState, useEffect } from "react";

const SIGNAL_STYLES = {
  CALIBRATING: "bg-slate-600 text-slate-300",
  STRONG: "bg-green-500 text-white",
  MODERATE: "bg-amber-500 text-white",
  WEAK: "bg-red-500 text-white",
};

const DIRECTION_ICONS = { RISING: "▲", FALLING: "▼", STABLE: "→" };
const DIRECTION_COLORS = { RISING: "text-green-400", FALLING: "text-red-400", STABLE: "text-slate-400" };

export default function SignalBar() {
  const [confluence, setConfluence] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);

  useEffect(() => {
    fetch("/api/signals/confluence").then(r => r.json()).then(setConfluence);
  }, []);

  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws`);
    ws.onopen = () => setWsConnected(true);
    ws.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setConfluence(data.confluence);
    };
    ws.onclose = () => setWsConnected(false);
    return () => ws.close();
  }, []);

  const overall = confluence?.overall_score ?? 0;
  const signal = confluence?.signal ?? "CALIBRATING";
  const direction = confluence?.direction ?? "STABLE";
  const narrative = confluence?.narrative ?? "";
  const calibration = confluence?.calibration_progress;
  const isCalibrating = confluence?.calibration_status === "calibrating";

  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 md:p-6 mb-4">
      <div className="flex items-center gap-4">
        <div className={`px-3 py-1.5 rounded font-bold text-sm ${SIGNAL_STYLES[signal]}`}>
          {signal}
          {!isCalibrating && <span className={`ml-2 ${DIRECTION_COLORS[direction]}`}>{DIRECTION_ICONS[direction]}</span>}
        </div>
        <div className="flex-1">
          <div className="text-xs text-slate-500 mb-1">Confluence Score</div>
          {isCalibrating ? (
            <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div className="h-full bg-slate-600 rounded-full transition-all duration-500"
                   style={{ width: `${(calibration?.conditions_met || 0) / (calibration?.conditions_total || 4) * 100}%` }} />
            </div>
          ) : (
            <div className="h-3 bg-[#1e1e2e] rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-red-500 via-amber-500 to-emerald-500 rounded-full transition-all duration-700"
                   style={{ width: `${(overall * 100).toFixed(0)}%` }} />
            </div>
          )}
        </div>
        <div className="text-2xl md:text-3xl font-mono font-bold text-cyan-400">
          {isCalibrating ? "--" : `${(overall * 100).toFixed(0)}%`}
        </div>
      </div>

      {narrative && (
        <p className="mt-2 text-sm text-slate-300">{narrative}</p>
      )}

      {isCalibrating && calibration && (
        <div className="mt-3 grid grid-cols-2 md:grid-cols-4 gap-2 text-xs text-slate-500">
          {Object.entries(calibration.conditions || {}).map(([key, cond]) => (
            <div key={key} className={`text-center ${cond.met ? "text-green-400" : "text-slate-500"}`}>
              <div>{key.replace(/_/g, " ")}</div>
              <div className="font-mono">{cond.met ? "✓" : cond.current != null ? `${cond.current}/${cond.target}` : "—"}</div>
            </div>
          ))}
        </div>
      )}

      {!isCalibrating && confluence?.components?.length > 0 && (
        <div className="grid grid-cols-2 gap-2 mt-3 text-xs text-slate-400">
          {confluence.components.map((c) => (
            <div key={c.name} className="text-center" title={c.detail}>
              <div className="text-[10px] uppercase">{c.name}</div>
              <div className="font-mono text-white">{(c.score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      )}

      <div className="mt-2 text-[10px] text-right">
        <span className={wsConnected ? "text-green-500" : "text-red-500"}>●</span>
        <span className="text-slate-600 ml-1">{wsConnected ? "live" : "polling"}</span>
      </div>
    </div>
  );
}
