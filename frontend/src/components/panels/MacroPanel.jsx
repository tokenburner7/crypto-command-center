import { useState, useEffect, useRef, useCallback } from "react";
import { createChart } from "lightweight-charts";

export default function MacroPanel() {
  const containerRef = useRef(null);
  const [latest, setLatest] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchLatest = useCallback(() => {
    fetch("/api/macro/latest").then(r => r.json()).then(setLatest).catch(() => {});
  }, []);

  useEffect(() => {
    fetchLatest();
    const t = setInterval(fetchLatest, 300000);
    return () => clearInterval(t);
  }, [fetchLatest]);

  useEffect(() => {
    if (!containerRef.current) return;
    const chart = createChart(containerRef.current, {
      width: containerRef.current.clientWidth,
      height: 220,
      layout: { background: { color: "#13131a" }, textColor: "#94a3b8" },
      grid: { vertLines: { color: "#1e1e2e" }, horzLines: { color: "#1e1e2e" } },
      timeScale: { timeVisible: false },
      crosshair: { mode: 0 },
    });

    Promise.all([
      fetch("/api/macro/history?indicator=BTC&hours=168").then(r => r.json()),
      fetch("/api/macro/history?indicator=DXY&hours=168").then(r => r.json()),
    ])
      .then(([btc, dxy]) => {
        const btcSeries = chart.addLineSeries({ color: "#f7931a", lineWidth: 2, priceFormat: { type: "price", minMove: 0.01 } });
        const dxySeries = chart.addLineSeries({ color: "#06b6d4", lineWidth: 1, priceScaleId: "dxy" });
        chart.priceScale("dxy").applyOptions({ borderColor: "#06b6d4", textColor: "#06b6d4" });
        btcSeries.setData((btc || []).map(d => ({ time: Math.floor(d.timestamp), value: d.value })));
        dxySeries.setData((dxy || []).map(d => ({ time: Math.floor(d.timestamp), value: d.value })));
        setLoading(false);
      })
      .catch(e => { setError(e.message); setLoading(false); });

    const observer = new ResizeObserver(() => {
      if (containerRef.current) chart.applyOptions({ width: containerRef.current.clientWidth });
    });
    observer.observe(containerRef.current);
    return () => { observer.disconnect(); chart.remove(); };
  }, []);

  const icons = { DXY: "💵", SP500: "📈", GOLD: "🥇", FEDFUNDS: "🏦", BTC: "₿", ETH: "Ξ" };

  if (error) return <p className="text-red-400 text-xs">Chart error: {error}</p>;

  return (
    <div>
      <div className="flex gap-2 mb-2 flex-wrap">
        {latest.map(d => (
          <div key={d.indicator} className="bg-[#1e1e2e] px-2 py-1 rounded text-xs">
            <span>{icons[d.indicator] || ""}</span>{" "}
            <span className="text-slate-400">{d.indicator}</span>{" "}
            <span className="text-white font-mono">
              {d.value > 1000 ? `$${d.value.toLocaleString()}` : d.value.toFixed(2)}
            </span>
          </div>
        ))}
      </div>
      {loading && <p className="text-slate-500 text-xs">Loading chart...</p>}
      <div ref={containerRef} className="w-full" />
    </div>
  );
}
