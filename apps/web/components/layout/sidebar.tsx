"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

const navItems = [
  { href: "/", label: "Agent Console", icon: "◈" },
  { href: "/runs", label: "Trace Viewer", icon: "◉" },
  { href: "/knowledge", label: "Knowledge Base", icon: "◎" },
  { href: "/evaluation", label: "Evaluation", icon: "◆" },
  { href: "/safety", label: "Safety Guard", icon: "△" },
  { href: "/settings", label: "Settings", icon: "◌" },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={`fixed left-0 top-0 z-40 flex h-full flex-col border-r transition-all duration-200 ${
        collapsed ? "w-14" : "w-60"
      }`}
      style={{
        background: "var(--bg-card)",
        borderColor: "var(--border)",
      }}
    >
      {/* Logo */}
      <div className="flex h-14 items-center gap-3 border-b px-4" style={{ borderColor: "var(--border-light)" }}>
        <div
          className="flex h-8 w-8 items-center justify-center rounded-lg text-sm font-bold text-white"
          style={{ background: "var(--accent)" }}
        >
          R
        </div>
        {!collapsed && (
          <div className="min-w-0">
            <p className="text-sm font-semibold" style={{ color: "var(--text-primary)" }}>
              R&D Agent
            </p>
            <p className="text-[10px] font-medium uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>
              Copilot
            </p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-all ${
                isActive
                  ? "bg-brand-50 text-brand-700 dark:bg-brand-950 dark:text-brand-300"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
              }`}
              title={collapsed ? item.label : undefined}
            >
              <span className="flex h-5 w-5 items-center justify-center text-base">{item.icon}</span>
              {!collapsed && <span>{item.label}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Bottom: collapse toggle + env info */}
      <div className="border-t px-3 py-3" style={{ borderColor: "var(--border-light)" }}>
        {!collapsed && (
          <div className="mb-3 space-y-1 px-1">
            <p className="text-[10px] font-semibold uppercase tracking-wider" style={{ color: "var(--text-tertiary)" }}>
              Environment
            </p>
            <div className="flex flex-wrap gap-1.5">
              <span className="badge-slate text-[10px]">Local</span>
              <span className="badge-slate text-[10px]">Mock</span>
              <span className="badge-brand text-[10px]">DeepSeek</span>
            </div>
          </div>
        )}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="flex w-full items-center justify-center rounded-lg px-3 py-2 text-xs font-medium text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-800"
        >
          {collapsed ? "→" : "← 收起"}
        </button>
      </div>
    </aside>
  );
}
