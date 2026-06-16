import { useState, useEffect } from "react";

export default function OnChainPanel() {
  const [whales, setWhales] = useState([]);
  const [stats, setStats] = useState(null);
  const [chain, setChain] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    const params = new URLSearchParams({ limit: "10", min_usd: "500000" });
    if (chain) params.set("blockchain", chain);
    
    Promise.all([
      fetch(`/api/onchain/whales?${params}`).then(r => r.json()),
      fetch("/api/onchain/stats").then(r => r.json()),
    ])
      .then(([w, s]) => { setWhales(w); setStats(s); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 60000); return () => clearInterval(t); }, [chain]);

  const formatUsd = (v) => v >= 1e9 ? `$${(v/1e9).toFixed(1)}B` : v >= 1e6 ? `$${(v/1e6).toFixed(1)}M` : `$${v.toFixed(0)}`;

  return (
    <div>
      <div className="flex gap-2 mb-3">
        {[null, "bitcoin", "ethereum"].map(c => (
          <button key={c ?? "all"} onClick={() => { setChain(c); setLoading(true); }}
                  className={`text-xs px-2 py-1 rounded ${chain === c ? "bg-cyan-500/20 text-cyan-400" : "bg-[#1e1e2e] text-slate-400 hover:text-white"}`}>
            {c ? c[0].toUpperCase() + c.slice(1) : "All"}
          </button>
        ))}
      </div>

      {stats && (
        <div className="flex gap-3 mb-3 text-xs">
          <span className="text-slate-500">24h: <b className="text-cyan-400">{stats.total}</b></span>
          <span className="text-slate-500">Max: <b className="text-white">{formatUsd(stats.max_amount)}</b></span>
        </div>
      )}

      {loading && <p className="text-slate-500 text-xs">Loading...</p>}
      {error && <p className="text-red-400 text-xs">Error: {error}</p>}
      {!loading && !error && whales.length === 0 && <p className="text-slate-600 text-xs">No whale activity in this window</p>}
      {!loading && !error && whales.length > 0 && (
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {whales.map(w => (
            <div key={w.tx_hash} className="flex justify-between text-xs border-b border-[#1e1e2e] pb-1">
              <span className="text-slate-500 w-12">{w.blockchain === "ethereum" ? "Ξ" : "₿"}</span>
              <span className="text-slate-400 font-mono flex-1 truncate">{w.tx_hash.slice(0, 12)}...</span>
              <span className="text-cyan-400 font-mono">{formatUsd(w.amount_usd)}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
