import { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center bg-[#0a0a0f]">
          <div className="bg-[#13131a] border border-[#1e1e2e] rounded-lg p-8 max-w-md text-center">
            <h2 className="text-red-400 text-lg font-bold mb-2">Something went wrong</h2>
            <p className="text-slate-400 text-sm mb-4">
              The dashboard encountered an error. This is usually temporary.
            </p>
            <pre className="text-xs text-slate-600 bg-[#0a0a0f] p-3 rounded mb-4 text-left overflow-auto max-h-32">
              {this.state.error?.message || "Unknown error"}
            </pre>
            <button
              onClick={() => { this.setState({ hasError: false }); window.location.reload(); }}
              className="px-4 py-2 bg-cyan-500/20 text-cyan-400 rounded text-sm hover:bg-cyan-500/30 transition-colors"
            >
              Reload Dashboard
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
