import { CheckCircle2, Clock, Filter, Download, MessageSquare, MapPin } from "lucide-react";
import React, { useState } from "react";
import { AlertRecord, HealthStatus, AlertLevel } from "@/src/types";
import { alerts as alertsData } from "@/src/data/dashboardMock";
import { cn } from "@/src/lib/utils";

/* ─── Mock Signalements Data ─── */
interface Signalement {
  id: string;
  institution: string;
  author: string;
  role: string;
  issue: string;
  timestamp: string;
  status: 'Nouveau' | 'En traitement' | 'Résolu';
}

const signalementsMock: Signalement[] = [
  { id: 'SIG-101', institution: 'FST', author: 'Dr. Karima', role: 'Professeur', issue: 'Équipement manquant : Vidéoprojecteur Amphi A défectueux depuis 2 semaines.', timestamp: 'Il y a 1 heure', status: 'Nouveau' },
  { id: 'SIG-102', institution: 'INSAT', author: 'Sami B.', role: 'Chef de département', issue: 'Fuite d\'eau détectée au 2ème étage, bloc C. Intervention urgente nécessaire.', timestamp: 'Il y a 3 heures', status: 'En traitement' },
  { id: 'SIG-103', institution: 'IHEC', author: 'Noura T.', role: 'Scolarité', issue: 'Problème d\'accès au portail étudiant pour les inscriptions M1.', timestamp: 'Il y a 5 heures', status: 'Nouveau' },
  { id: 'SIG-104', institution: 'ENIT', author: 'Comité Étudiant', role: 'Représentant', issue: 'Manque de chaises dans la salle de lecture de la bibliothèque centrale.', timestamp: 'Hier', status: 'Nouveau' },
  { id: 'SIG-105', institution: 'SUPCOM', author: 'Responsable IT', role: 'Staff technique', issue: 'Panne de la fibre principale réseau UCAR sur le campus.', timestamp: 'Hier', status: 'Résolu' },
];

export function Alerts() {
  const [activeTab, setActiveTab] = useState<'alertes' | 'signalements'>('alertes');
  
  // Alertes State
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
          <h2 className="text-xl tracking-tight font-semibold text-[#0F172A]">Centre d'opérations</h2>
          <p className="text-sm text-slate-500 mt-1">Supervision centralisée des alertes réseau et retours terrain.</p>
        </div>
        <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm font-medium text-[#1d5394] hover:bg-[#F0F5FA] transition-colors duration-100">
          <Download size={14} /> Exporter Synthèse
        </button>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-8 -mb-px">
          {([
            { key: 'alertes' as const, label: 'Alertes Système', count: alerts.filter(a => a.status !== 'resolved').length },
            { key: 'signalements' as const, label: 'Signalements Terrain', count: signalementsMock.filter(s => s.status === 'Nouveau').length },
          ]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'pb-3 text-sm font-medium transition-colors duration-150 border-b-2',
                activeTab === tab.key
                  ? 'text-[#0F172A] border-[#1d5394]'
                  : 'text-slate-500 hover:text-slate-700 border-transparent'
              )}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={cn(
                  'ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-tabular bg-red-100 text-red-700'
                )}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* ─── ALERTES SYSTÈME TAB ─── */}
      {activeTab === 'alertes' && (
        <div className="space-y-4">
          <div className="bg-white px-4 py-3 border border-slate-200 rounded-lg flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Filter size={14} className="text-slate-400" />
              <div className="flex gap-2">
                <FilterButton active={filter === 'all'} onClick={() => setFilter('all')}>Catalogue complet</FilterButton>
                <FilterButton active={filter === 'critical'} onClick={() => setFilter('critical')} variant="critical">Urgence Critique</FilterButton>
                <FilterButton active={filter === 'warning'} onClick={() => setFilter('warning')} variant="warning">Avertissement</FilterButton>
              </div>
            </div>
            <span className="text-xs font-medium text-slate-400"><Clock size={12} className="inline mr-1 mb-0.5" />Temps réel</span>
          </div>

          <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
            <div className="divide-y divide-slate-100">
              {filteredAlerts.map((alert) => (
                <div
                  key={alert.id}
                  className={cn(
                    "p-5 transition-colors duration-150",
                    alert.severity === 'critical' ? 'hover:bg-red-50/30' : 'hover:bg-amber-50/30'
                  )}
                >
                  <div className="flex flex-col md:flex-row justify-between gap-5">
                    <div className="flex items-start gap-4">
                      <div className="relative mt-2">
                        <div className={cn(
                          'w-2.5 h-2.5 rounded-full shrink-0 relative z-10',
                          alert.severity === 'critical' ? 'bg-red-600' : 'bg-amber-500'
                        )} />
                        {alert.severity === 'critical' && alert.status !== 'resolved' && (
                           <div className="absolute inset-0 w-2.5 h-2.5 bg-red-600 rounded-full animate-pulse-critical" />
                        )}
                      </div>

                      <div className="space-y-2.5">
                        <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                          <span className="text-[10px] font-bold bg-[#1d5394]/10 px-2 py-0.5 rounded text-[#1d5394] uppercase tracking-wider">
                            {alert.institutionCode}
                          </span>
                          <AlertTypeBadge type={alert.alertType} />
                          <LevelBadge level={alert.level} />
                          <span className="text-xs text-slate-400">— {alert.domain}</span>
                        </div>

                        <div>
                          <h3 className="text-sm font-semibold text-[#0F172A]">{alert.title}</h3>
                          <p className="text-[13px] text-slate-500 mt-1 leading-relaxed max-w-3xl">{alert.description}</p>
                        </div>
                      </div>
                    </div>

                    <div className="flex flex-col md:items-end gap-3 shrink-0 justify-center">
                      <span className="text-[11px] text-slate-400 font-medium">Détecté {alert.ageLabel}</span>
                      <div className="flex items-center gap-2">
                        <StatusBadge status={alert.status} />

                        {alert.status === 'pending' && (
                          <button
                            onClick={() => handleInProgress(alert.id)}
                            className="px-3 py-1 bg-[#1d5394] text-white text-[11px] font-semibold rounded-md hover:bg-[#153d6e] transition-colors duration-150 shadow-sm"
                          >
                            Initier 
                          </button>
                        )}
                        {alert.status === 'in_progress' && (
                          <button
                            onClick={() => handleResolve(alert.id)}
                            className="px-3 py-1 bg-emerald-600 text-white text-[11px] font-semibold rounded-md hover:bg-emerald-700 transition-colors duration-150 shadow-sm"
                          >
                            Clôturer
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
              
              {filteredAlerts.length === 0 && (
                <div className="text-center py-20 bg-white">
                  <CheckCircle2 size={32} className="mx-auto text-emerald-500 mb-3" />
                  <p className="text-slate-600 font-medium text-sm">Zone sécurisée. Aucune alerte système.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ─── SIGNALEMENTS TERRAIN TAB ─── */}
      {activeTab === 'signalements' && (
        <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 bg-slate-50/50 flex justify-between items-center">
            <h3 className="text-sm font-semibold text-[#0F172A]">Dépêches et incidents signalés par le personnel</h3>
            <span className="text-xs text-slate-400">{signalementsMock.length} tickets</span>
          </div>
          <div className="divide-y divide-slate-100">
             {signalementsMock.map((sig) => (
               <div key={sig.id} className="p-6 hover:bg-slate-50/50 transition-colors duration-150">
                 <div className="flex items-start gap-4">
                   <div className="w-10 h-10 rounded-full bg-slate-100 flex items-center justify-center shrink-0 border border-slate-200">
                     <MessageSquare size={16} className="text-slate-500" />
                   </div>
                   <div className="flex-1">
                     <div className="flex justify-between items-start">
                       <div className="flex items-center gap-2 mb-1">
                         <span className="text-[13px] font-semibold text-[#0F172A]">{sig.author}</span>
                         <span className="text-[11px] text-slate-400 px-1.5 border border-slate-200 rounded">{sig.role}</span>
                         <span className="flex items-center gap-1 text-[11px] font-medium text-[#1d5394]">
                           <MapPin size={10} /> {sig.institution}
                         </span>
                       </div>
                       <span className="text-[11px] text-slate-400">{sig.timestamp}</span>
                     </div>
                     <p className="text-[13px] text-slate-600 leading-relaxed max-w-3xl mt-1">{sig.issue}</p>
                     
                     <div className="flex items-center gap-3 mt-4">
                       <span className={cn(
                         "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded",
                         sig.status === 'Nouveau' ? "bg-red-50 text-red-600 border border-red-100" :
                         sig.status === 'En traitement' ? "bg-amber-50 text-amber-600 border border-amber-100" :
                         "bg-slate-50 text-slate-500 border border-slate-200"
                       )}>
                         {sig.status}
                       </span>
                       <button className="text-[11px] font-semibold text-[#1d5394] hover:underline">
                         Assigner un technicien →
                       </button>
                     </div>
                   </div>
                 </div>
               </div>
             ))}
          </div>
        </div>
      )}
    </div>
  );
}

function FilterButton({ children, active, onClick, variant = "info" }: { children: React.ReactNode, active: boolean, onClick: () => void, variant?: HealthStatus | "info" }) {
  const styles: Record<string, string> = {
    info: active ? "bg-slate-800 text-white border-transparent" : "text-slate-600 hover:bg-slate-100 border-transparent",
    critical: active ? "bg-red-50 text-red-700 border-red-200 font-semibold" : "text-slate-600 hover:bg-slate-100 border-transparent",
    warning: active ? "bg-amber-50 text-amber-700 border-amber-200 font-semibold" : "text-slate-600 hover:bg-slate-100 border-transparent",
  };

  return (
    <button 
      onClick={onClick}
      className={cn("px-3 py-1.5 rounded-md text-[11px] font-medium transition-colors duration-150 border", styles[variant])}
    >
      {children}
    </button>
  );
}

function AlertTypeBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    THRESHOLD: 'bg-blue-50/50 text-blue-700 border-blue-200',
    ANOMALY: 'bg-purple-50/50 text-purple-700 border-purple-200',
    DOCUMENT: 'bg-slate-50/50 text-slate-700 border-slate-200',
    PREDICTIVE: 'bg-indigo-50/50 text-indigo-700 border-indigo-200',
    COMPLIANCE: 'bg-amber-50/50 text-amber-700 border-amber-200',
  };
  return (
    <span className={cn('px-1.5 py-0.5 rounded flex items-center text-[9px] font-bold uppercase tracking-wider border', styles[type] || styles.THRESHOLD)}>
      {type}
    </span>
  );
}

function LevelBadge({ level }: { level: AlertLevel }) {
  const styles: Record<string, string> = {
    INFO: 'text-blue-500',
    WARNING: 'text-amber-500',
    CRITICAL: 'text-red-500',
    PREDICTIVE: 'text-indigo-500',
  };
  return (
    <span className={cn('px-1 py-0.5 flex items-center text-[9px] font-bold tracking-wider', styles[level])}>
      — {level}
    </span>
  );
}

function StatusBadge({ status }: { status: AlertRecord['status'] }) {
  const configs = {
    pending: { label: "À assigner", style: "text-slate-400" },
    in_progress: { label: "En cours", style: "text-amber-500" },
    resolved: { label: "Résolu", style: "text-emerald-500" }
  };
  const config = configs[status];
  return (
    <span className={cn("text-[11px] font-medium mr-2", config.style)}>
      {config.label}
    </span>
  );
}
