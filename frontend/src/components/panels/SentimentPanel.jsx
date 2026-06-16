import { useState, useEffect } from "react";

export default function SentimentPanel() {
  const [trend, setTrend] = useState(null);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchData = () => {
    Promise.all([
      fetch("/api/sentiment/trend").then(r => r.json()),
      fetch("/api/sentiment/scores?limit=5").then(r => r.json()),
    ])
      .then(([t, p]) => { setTrend(t); setPosts(p); setError(null); })
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchData(); const t = setInterval(fetchData, 120000); return () => clearInterval(t); }, []);

  if (loading) return <p className="text-slate-500 text-xs">Loading...</p>;
  if (error) return <p className="text-red-400 text-xs">{error}</p>;

  const score = trend?.avg_score ?? 0;
  const count = trend?.count ?? 0;
  const baseline = trend?.avg_baseline;
  const gaugeAngle = (score + 1) * 90;

  return (
    <div>
      {/* Summary */}
      <div className="flex items-center gap-3 mb-3">
        <div className="relative w-16 h-8 overflow-hidden">
          <div className="absolute bottom-0 left-0 w-full h-16 rounded-t-full bg-[#1e1e2e]">
            <div
              className="absolute bottom-0 left-1/2 w-1 h-8 bg-gradient-to-t from-red-500 via-amber-400 to-green-400 origin-bottom transition-transform duration-500"
              style={{ transform: `rotate(${gaugeAngle - 90}deg)` }}
            />
          </div>
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-xs font-bold text-white">
            {score > 0.1 ? "🐂" : score < -0.1 ? "🐻" : "➖"}
          </div>
        </div>
        <div>
          <div className="text-xs text-slate-500">{count} posts · {(score * 100).toFixed(0)}% net</div>
          {baseline && (
            <div className="text-[10px] text-slate-600">
              vs Fear & Greed: {baseline} <span className="text-slate-500">({baseline > 50 ? "greed" : baseline < 50 ? "fear" : "neutral"})</span>
            </div>
          )}
        </div>
      </div>

      {/* Posts */}
      {posts.length === 0 ? (
        <p className="text-slate-600 text-xs">No sentiment data yet</p>
      ) : (
        <div className="space-y-1 max-h-40 overflow-y-auto">
          {posts.map((p, i) => (
            <div key={i} className="text-xs border-b border-[#1e1e2e] pb-1">
              <div className="flex justify-between">
                <span className={`font-mono ${p.score > 0 ? "text-green-400" : p.score < 0 ? "text-red-400" : "text-slate-400"}`}>
                  {(p.score * 100).toFixed(0)}%
                </span>
                <span className="text-slate-500">{p.source}</span>
              </div>
              <div className="text-slate-400 truncate">{p.summary}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
