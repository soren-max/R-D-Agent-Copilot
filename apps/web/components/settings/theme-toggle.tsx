"use client";

import { useEffect, useState } from "react";
import type { ThemeMode } from "@/lib/mock/settings";

type Props = {
  current: ThemeMode;
  onToggle?: (mode: ThemeMode) => void;
};

export function ThemeToggle({ current }: Props) {
  const [mode, setMode] = useState<ThemeMode>(current);

  useEffect(() => {
    const cls = document.documentElement.classList;
    if (mode === "dark") cls.add("dark");
    else if (mode === "light") cls.remove("dark");
    else {
      const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
      cls.toggle("dark", prefersDark);
    }
  }, [mode]);

  const options: ThemeMode[] = ["light", "dark", "system"];

  return (
    <div className="card">
      <div className="card-header"><h3 className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>Theme</h3></div>
      <div className="card-body">
        <div className="flex gap-2">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => setMode(opt)}
              className={`flex-1 rounded-xl border-2 px-4 py-3 text-center text-sm font-medium transition-all ${
                mode === opt ? "border-indigo-400 bg-indigo-50/50 dark:border-indigo-600" : "border-slate-200 hover:border-slate-300 dark:border-slate-700"
              }`}
            >
              {opt === "light" ? "☀ Light" : opt === "dark" ? "☾ Dark" : "◐ System"}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
