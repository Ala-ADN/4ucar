import { AlertCircle, CheckCircle2, Clock, Filter, Download } from "lucide-react";
import { motion, AnimatePresence } from "motion/react";
import React, { useState } from "react";
import { Alert, HealthStatus } from "@/src/types";
import alertsData from "@/src/data/alerts.json";
import { Badge } from "@/src/components/ui/StatusDot";
import { cn } from "@/src/lib/utils";

export function Alerts() {
  const [alerts, setAlerts] = useState<Alert[]>(alertsData as Alert[]);
  const [filter, setFilter] = useState<HealthStatus | "all">("all");

  const filteredAlerts = alerts.filter(a => filter === "all" || a.severity === filter);

  function handleResolve(id: string) {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'resolved' } : a));
  }

  function handleInProgress(id: string) {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, status: 'in_progress' } : a));
  }

  return (
    <div className="space-y-8">
      <div className="flex justify-between items-end">
        <div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Poste de Commandement des Alertes</h2>
          <p className="text-slate-400 text-xs font-bold uppercase tracking-widest mt-1">Activité Réseau en Temps Réel</p>
        </div>
        <button className="flex items-center gap-2 px-5 py-2.5 bg-white border border-slate-200 shadow-sm rounded-xl text-[10px] font-bold uppercase tracking-widest text-slate-600 hover:bg-slate-50 transition-all">
          <Download size={14} /> Exporter Rapport
        </button>
      </div>

      <div className="bg-slate-900 px-6 py-4 rounded-2xl shadow-xl shadow-slate-900/10 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Filter size={14} className="text-slate-500" />
          <div className="flex gap-2">
            <FilterButton active={filter === 'all'} onClick={() => setFilter('all')}>Toutes les alertes</FilterButton>
            <FilterButton active={filter === 'critical'} onClick={() => setFilter('critical')} variant="critical">CRITIQUE</FilterButton>
            <FilterButton active={filter === 'warning'} onClick={() => setFilter('warning')} variant="warning">AVERTISSEMENT</FilterButton>
          </div>
        </div>
        <span className="text-[10px] font-black text-blue-500 uppercase tracking-tighter">Moniteur: CENTRAL-TUNIS</span>
      </div>

      <div className="bg-slate-50 border border-slate-200 rounded-2xl overflow-hidden shadow-sm">
        <div className="bg-white px-8 py-5 border-b border-slate-200 flex justify-between items-center">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-600">Flux des Incidents</h3>
            <span className="text-[10px] font-bold text-slate-400 uppercase">{filteredAlerts.length} ÉLÉMENTS DÉTECTÉS</span>
        </div>
        <div className="divide-y divide-slate-200">
          <AnimatePresence mode="popLayout">
            {filteredAlerts.map((alert) => (
              <motion.div
                layout
                key={alert.id}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="bg-white p-6 hover:bg-slate-50/50 transition-all group"
              >
                <div className="flex flex-col md:flex-row justify-between gap-8">
                  <div className="flex items-start gap-6">
                    <div className={cn(
                      "w-4 h-4 rounded-full mt-1 shrink-0 flex items-center justify-center",
                      alert.severity === 'critical' ? "bg-red-500 shadow-[0_0_12px_rgba(239,68,68,0.4)] animate-pulse" : "bg-status-high"
                    )}>
                       <div className="w-1 h-1 bg-white rounded-full opacity-60" />
                    </div>
                    
                    <div className="space-y-4">
                      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
                        <span className="text-xs font-mono bg-slate-100 px-3 py-1 rounded text-slate-600 font-bold tracking-tight">NODE: {alert.institution}</span>
                        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{alert.domain}</span>
                        <div className="flex items-center gap-2 text-slate-400">
                           <Clock size={12} />
                           <span className="text-[10px] font-bold uppercase tracking-tighter">{alert.time}</span>
                        </div>
                      </div>
                      
                      <div>
                        <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors">{alert.title}</h3>
                        <p className="text-sm text-slate-500 mt-2 leading-relaxed max-w-3xl">{alert.description}</p>
                      </div>
                    </div>
                  </div>

                  <div className="flex flex-col items-end gap-5 shrink-0 justify-center">
                    <StatusBadge status={alert.status} />
                    
                    <div className="flex gap-2">
                      {alert.status === 'pending' && (
                        <button 
                          onClick={() => handleInProgress(alert.id)}
                          className="px-5 py-2.5 bg-slate-900 text-white text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-slate-800 transition-all shadow-lg shadow-black/10"
                        >
                          INTERVENIR
                        </button>
                      )}
                      {alert.status === 'in_progress' && (
                        <button 
                          onClick={() => handleResolve(alert.id)}
                          className="px-5 py-2.5 bg-status-good text-white text-[10px] font-black uppercase tracking-widest rounded-lg hover:bg-green-600 transition-all shadow-lg shadow-green-600/10 flex items-center gap-2"
                        >
                          RÉSOUDRE
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
          
          {filteredAlerts.length === 0 && (
            <div className="text-center py-32 bg-white">
              <CheckCircle2 size={48} className="mx-auto text-green-500/20 mb-6" />
              <p className="text-slate-400 font-bold uppercase tracking-widest text-xs tracking-[0.2em]">Périmètre de Sécurité Optimal ✓</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function FilterButton({ children, active, onClick, variant = "info" }: { children: React.ReactNode, active: boolean, onClick: () => void, variant?: HealthStatus | "info" }) {
  const styles: Record<string, string> = {
    info: active ? "bg-blue-600 text-white" : "text-slate-400 hover:text-slate-200",
    critical: active ? "bg-red-500 text-white" : "text-slate-400 hover:text-red-400",
    warning: active ? "bg-amber-500 text-white" : "text-slate-400 hover:text-amber-400",
  };

  return (
    <button 
      onClick={onClick}
      className={cn("px-4 py-2 rounded-lg text-[10px] font-black uppercase tracking-widest transition-all", styles[variant])}
    >
      {children}
    </button>
  );
}

function StatusBadge({ status }: { status: Alert['status'] }) {
  const configs = {
    pending: { label: "En file d'attente", style: "bg-slate-100 text-slate-400" },
    in_progress: { label: "En cours d'intervention", style: "bg-blue-50 text-blue-600 border border-blue-100" },
    resolved: { label: "Incident corrigé", style: "bg-green-50 text-green-600 border border-green-100" }
  };
  const config = configs[status];
  return (
    <span className={cn("px-3 py-1.5 rounded-lg text-[9px] font-black uppercase tracking-widest", config.style)}>
      {config.label}
    </span>
  );
}
