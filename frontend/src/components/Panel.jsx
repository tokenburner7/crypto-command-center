export default function Panel({ title, children, className = "" }) {
  return (
    <div className={`bg-[#13131a] border border-[#1e1e2e] rounded-lg p-4 ${className}`}>
      <h2 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-3">{title}</h2>
      {children}
    </div>
  );
}
