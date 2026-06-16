import { useState, useEffect } from "react";

const COLORS = { USDT: "#26a17b", USDC: "#2775ca", DAI: "#fab005", USDe: "#6366f1" };

export default function StablecoinPanel() {
  const [supply, setSupply] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    fetch("/api/stablecoin/supply")
      .then(r => r.json())
      .then(data => { setSupply(data); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, []);

  const maxSupply = Math.max(...supply.map(s => s.total_supply_usd || 0), 1);

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">Error: {error}</p>;
  if (!supply.length) return <p className="text-slate-600 text-xs">No supply data yet — collecting...</p>;

  return (
    <div className="space-y-3">
      {supply.map(s => (
        <div key={s.stablecoin}>
          <div className="flex justify-between text-xs mb-1">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full" style={{ background: COLORS[s.stablecoin] || "#6366f1" }} />
              <span className="text-slate-400">{s.stablecoin}</span>
            </div>
            <span className="text-white font-mono">${(s.total_supply_usd / 1e9).toFixed(1)}B</span>
            {s.change_24h_usd !== 0 && (
              <span className={`font-mono text-xs ${s.change_24h_usd > 0 ? "text-green-400" : "text-red-400"}`}>
                {s.change_24h_usd > 0 ? "+" : ""}${(Math.abs(s.change_24h_usd) / 1e6).toFixed(0)}M
              </span>
            )}
          </div>
          <div className="h-2 bg-[#1e1e2e] rounded-full overflow-hidden">
            <div className="h-full rounded-full transition-all"
                 style={{ width: `${((s.total_supply_usd || 0) / maxSupply) * 100}%`, background: COLORS[s.stablecoin] || "#6366f1" }} />
          </div>
        </div>
      ))}
    </div>
  );
}
