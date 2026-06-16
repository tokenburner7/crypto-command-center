import { useState } from "react";

export default function ExperimentalToggle({ label, children }) {
  const [enabled, setEnabled] = useState(false);
  
  if (!enabled) {
    return (
      <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{label}</h3>
            <p className="text-xs text-amber-500 mt-1">⚡ Experimental — opt-in to enable</p>
          </div>
          <button onClick={() => setEnabled(true)}
                  className="px-3 py-1.5 bg-amber-500/20 text-amber-400 rounded text-xs hover:bg-amber-500/30 transition-colors">
            Enable
          </button>
        </div>
      </div>
    );
  }
  
  return (
    <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider">{label}</h3>
        <div className="flex items-center gap-2">
          <span className="text-[10px] text-amber-500">EXPERIMENTAL</span>
          <button onClick={() => setEnabled(false)}
                  className="text-xs text-slate-500 hover:text-slate-300">Disable</button>
        </div>
      </div>
      {children}
    </div>
  );
}
