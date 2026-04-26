import { CheckCircle2, Clock, Filter, Download } from "lucide-react";
import React, { useState } from "react";
import { AlertRecord, HealthStatus, AlertLevel } from "@/src/types";
import { alerts as alertsData } from "@/src/data/dashboardMock";
import { cn } from "@/src/lib/utils";

export function Alerts() {
  const [alerts, setAlerts] = useState<AlertRecord[]>(alertsData);
  const [filter, setFilter] = useState<HealthStatus | "all">("all");

  const filteredAlerts = alerts.filter(a => filter === "all" || a.severity === filter);

  function handleResolve(id: string) {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a));
  }

  function handleInProgress(id: string) {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'in_progress' } : a));
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-semibold text-slate-900">Centre des alertes</h2>
          <p className="text-sm text-slate-600 mt-1">Activité réseau en temps réel</p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-300 rounded-md text-sm font-medium text-slate-700 hover:bg-slate-50 transition-colors duration-150">
          <Download size={14} /> Exporter Rapport
        </button>
      </div>

      <div className="bg-white px-4 py-3 border border-slate-200 rounded-md flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Filter size={14} className="text-slate-500" />
          <div className="flex gap-2">
            <FilterButton active={filter === 'all'} onClick={() => setFilter('all')}>Toutes les alertes</FilterButton>
            <FilterButton active={filter === 'critical'} onClick={() => setFilter('critical')} variant="critical">CRITIQUE</FilterButton>
            <FilterButton active={filter === 'warning'} onClick={() => setFilter('warning')} variant="warning">AVERTISSEMENT</FilterButton>
          </div>
        </div>
        <span className="text-xs font-medium text-slate-500">Moniteur: CENTRAL-TUNIS</span>
      </div>

      <div className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-base font-semibold text-slate-900">Flux des incidents</h3>
            <span className="text-sm text-slate-600">{filteredAlerts.length} éléments détectés</span>
        </div>
        <div className="divide-y divide-slate-200">
          {filteredAlerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white p-5"
            >
              <div className="flex flex-col md:flex-row justify-between gap-5">
                <div className="flex items-start gap-4">
                  <div className={cn(
                    'w-2.5 h-2.5 rounded-full mt-2 shrink-0',
                    alert.severity === 'critical' ? 'bg-red-600' : 'bg-amber-500'
                  )} />

                  <div className="space-y-2">
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                      <span className="text-xs font-medium bg-slate-100 px-2 py-1 rounded text-slate-700">NODE: {alert.institutionCode}</span>
                      <AlertTypeBadge type={alert.alertType} />
                      <LevelBadge level={alert.level} />
                      <span className="text-xs text-slate-500">{alert.domain}</span>
                      <div className="flex items-center gap-1.5 text-slate-500">
                        <Clock size={12} />
                        <span className="text-xs">{alert.ageLabel}</span>
                      </div>
                    </div>

                    <div>
                      <h3 className="text-base font-semibold text-slate-900">{alert.title}</h3>
                      <p className="text-sm text-slate-600 mt-1 leading-relaxed max-w-3xl">{alert.description}</p>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col md:items-end gap-3 shrink-0 justify-center">
                  <StatusBadge status={alert.status} />

                  <div className="flex gap-2">
                    {alert.status === 'pending' && (
                      <button
                        onClick={() => handleInProgress(alert.id)}
                        className="px-3 py-1.5 bg-blue-800 text-white text-sm font-medium rounded-md hover:bg-blue-900 transition-colors duration-150"
                      >
                        Intervenir
                      </button>
                    )}
                    {alert.status === 'in_progress' && (
                      <button
                        onClick={() => handleResolve(alert.id)}
                        className="px-3 py-1.5 bg-green-700 text-white text-sm font-medium rounded-md hover:bg-green-800 transition-colors duration-150"
                      >
                        Résoudre
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
          
          {filteredAlerts.length === 0 && (
            <div className="text-center py-20 bg-white">
              <CheckCircle2 size={40} className="mx-auto text-green-700 mb-4" />
              <p className="text-slate-700 font-medium text-sm">Aucune alerte pour ce filtre.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterButton({ children, active, onClick, variant = "info" }: { children: React.ReactNode, active: boolean, onClick: () => void, variant?: HealthStatus | "info" }) {
  const styles: Record<string, string> = {
    info: active ? "bg-blue-800 text-white border border-blue-800" : "text-slate-700 hover:bg-slate-100 border border-slate-300",
    critical: active ? "bg-red-700 text-white border border-red-700" : "text-slate-700 hover:bg-slate-100 border border-slate-300",
    warning: active ? "bg-amber-600 text-white border border-amber-600" : "text-slate-700 hover:bg-slate-100 border border-slate-300",
  };

  return (
    <button 
      onClick={onClick}
      className={cn("px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-150", styles[variant])}
    >
      {children}
    </button>
  );
}

function AlertTypeBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    THRESHOLD: 'bg-blue-50 text-blue-700 border-blue-200',
    ANOMALY: 'bg-purple-50 text-purple-700 border-purple-200',
    DOCUMENT: 'bg-slate-50 text-slate-700 border-slate-200',
    PREDICTIVE: 'bg-indigo-50 text-indigo-700 border-indigo-200',
    COMPLIANCE: 'bg-amber-50 text-amber-700 border-amber-200',
  };
  return (
    <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wide border', styles[type] || styles.THRESHOLD)}>
      {type}
    </span>
  );
}

function LevelBadge({ level }: { level: AlertLevel }) {
  const styles: Record<string, string> = {
    INFO: 'bg-blue-50 text-blue-600',
    WARNING: 'bg-amber-50 text-amber-600',
    CRITICAL: 'bg-red-50 text-red-600',
    PREDICTIVE: 'bg-indigo-50 text-indigo-600',
  };
  return (
    <span className={cn('px-1.5 py-0.5 rounded text-[10px] font-semibold', styles[level])}>
      {level}
    </span>
  );
}

function StatusBadge({ status }: { status: AlertRecord['status'] }) {
  const configs = {
    pending: { label: "En attente", style: "bg-slate-100 text-slate-700 border border-slate-200" },
    in_progress: { label: "En cours", style: "bg-blue-50 text-blue-800 border border-blue-200" },
    resolved: { label: "Résolu", style: "bg-green-50 text-green-800 border border-green-200" }
  };
  const config = configs[status];
  return (
    <span className={cn("px-2.5 py-1 rounded text-xs font-medium", config.style)}>
      {config.label}
    </span>
  );
}
