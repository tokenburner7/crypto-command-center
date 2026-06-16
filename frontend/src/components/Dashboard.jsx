import Panel from "./Panel";
import OnChainPanel from "./panels/OnChainPanel";
import StablecoinPanel from "./panels/StablecoinPanel";
import SentimentPanel from "./panels/SentimentPanel";
import MacroPanel from "./panels/MacroPanel";
import SignalBar from "./SignalBar";
import ExperimentalToggle from "./ExperimentalToggle";

export default function Dashboard() {
  return (
    <div className="min-h-screen p-4 md:p-6 max-w-7xl mx-auto">
      <header className="mb-4">
        <h1 className="text-2xl font-bold text-cyan-400">Crypto Command Center</h1>
        <p className="text-slate-500 text-xs">On-Chain Intelligence · Stablecoin Flows</p>
      </header>
      <SignalBar />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <Panel title="On-Chain Intelligence"><OnChainPanel /></Panel>
        <Panel title="Stablecoin Flows"><StablecoinPanel /></Panel>
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <ExperimentalToggle label="AI Sentiment">
          <SentimentPanel />
        </ExperimentalToggle>
        <ExperimentalToggle label="Macro × Crypto">
          <MacroPanel />
        </ExperimentalToggle>
      </div>
    </div>
  );
}
