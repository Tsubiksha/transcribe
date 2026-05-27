import React, { Component } from "react";

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("Frontend render failed", error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <main className="grid min-h-screen place-items-center bg-mist p-4">
          <section className="panel max-w-2xl space-y-3">
            <h1 className="text-xl font-bold text-red-700">Frontend error</h1>
            <p className="text-sm text-slate-700">
              A component failed while rendering. The message below is shown so the page never fails silently.
            </p>
            <pre className="max-h-64 overflow-auto rounded-md bg-slate-950 p-3 text-xs text-white">
              {this.state.error?.stack || this.state.error?.message || String(this.state.error)}
            </pre>
            <button className="btn-primary" onClick={() => window.location.assign("/login")}>
              Back to login
            </button>
          </section>
        </main>
      );
    }

    return this.props.children;
  }
}
