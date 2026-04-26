import React from 'react';
import { cn } from "@/src/lib/utils";
import { HealthStatus } from "@/src/types";

export function StatusDot({ status, animate = false }: { status: HealthStatus, animate?: boolean }) {
  const colors = {
    good: "bg-status-good",
    warning: "bg-status-medium",
    critical: "bg-status-critical"
  };

  return (
    <div className="relative flex items-center justify-center">
      {animate && status === 'critical' && (
        <span className="absolute inline-flex h-full w-full rounded-full bg-status-critical opacity-30"></span>
      )}
      <div className={cn("w-2.5 h-2.5 rounded-full border border-white", colors[status])} />
    </div>
  );
}

export function Badge({ children, variant = "info" }: { children: React.ReactNode, variant?: HealthStatus | "info" | "purple" | "amber" }) {
  const styles: Record<string, string> = {
    info: "bg-blue-50 text-blue-700",
    good: "bg-green-50 text-green-700",
    warning: "bg-amber-50 text-amber-700",
    critical: "bg-red-50 text-red-700",
    purple: "bg-slate-100 text-slate-700",
    amber: "bg-amber-100 text-amber-700"
  };

  return (
    <span className={cn("px-2 py-0.5 rounded text-xs font-medium", styles[variant])}>
      {children}
    </span>
  );
}
