"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";

export function TriggerButton() {
  const [state, setState] = useState<"idle" | "loading" | "done" | "error">("idle");

  async function trigger() {
    setState("loading");
    try {
      const res = await fetch("http://localhost:8000/signals/mf/trigger", { method: "POST" });
      setState(res.ok ? "done" : "error");
      if (res.ok) setTimeout(() => setState("idle"), 4000);
    } catch {
      setState("error");
    }
  }

  return (
    <button
      onClick={trigger}
      disabled={state === "loading"}
      className="flex items-center gap-2 rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition hover:bg-sky-500 disabled:opacity-60"
    >
      <RefreshCw size={14} className={state === "loading" ? "animate-spin" : ""} />
      {state === "loading" ? "Running…" : state === "done" ? "Queued ✓" : state === "error" ? "Failed" : "Recompute"}
    </button>
  );
}
