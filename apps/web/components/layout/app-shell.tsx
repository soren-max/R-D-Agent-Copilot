"use client";

import type { ReactNode } from "react";
import { Sidebar } from "./sidebar";
import { TopHeader } from "./top-header";

type AppShellProps = {
  children: ReactNode;
  title?: string;
};

export function AppShell({ children, title = "Agent Console" }: AppShellProps) {
  return (
    <div className="flex min-h-screen" style={{ background: "var(--bg-page)" }}>
      <Sidebar />
      <div className="ml-60 flex flex-1 flex-col transition-all duration-200">
        <TopHeader title={title} />
        <main className="flex-1 px-6 py-5 lg:px-8">
          {children}
        </main>
      </div>
    </div>
  );
}
