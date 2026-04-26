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
  { id: 'SIG-101', institution: 'FST', author: 'Dr. Ammar', role: 'Dép. Informatique', issue: 'Équipement manquant : Vidéoprojecteur Amphi A défectueux depuis 2 semaines. Cours de M1 impactés.', timestamp: 'Il y a 1 heure', status: 'Nouveau' },
  { id: 'SIG-102', institution: 'INSAT', author: 'Sami B.', role: 'Chef de département', issue: 'Fuite d\'eau détectée au 2ème étage, bloc C. Intervention urgente nécessaire avant dégradation des équipements.', timestamp: 'Il y a 3 heures', status: 'En traitement' },
  { id: 'SIG-103', institution: 'IHEC', author: 'Noura T.', role: 'Scolarité', issue: 'Problème d\'accès au portail étudiant pour les inscriptions Master 1. Signalé par +40 étudiants.', timestamp: 'Il y a 5 heures', status: 'Nouveau' },
  { id: 'SIG-104', institution: 'ENIT', author: 'Dr. Khaled M.', role: 'Représentant syndical', issue: 'Manque de chaises dans la salle de lecture de la bibliothèque centrale. Capacité réduite à 60%.', timestamp: 'Hier', status: 'Nouveau' },
  { id: 'SIG-105', institution: 'SUPCOM', author: 'Responsable IT', role: 'Staff technique', issue: 'Panne de la fibre principale réseau UCAR sur le campus. Connectivité dégradée depuis 14h.', timestamp: 'Hier', status: 'Résolu' },
  { id: 'SIG-106', institution: 'EPT', author: 'Comité Étudiant', role: 'Représentant', issue: 'Climatisation en panne dans le bâtiment B depuis 3 jours. Température mesurée : 38°C.', timestamp: 'Il y a 2 jours', status: 'En traitement' },
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
        <button className="flex items-center gap-2 px-3 py-1.5 bg-white border border-slate-200 rounded-md text-sm font-medium text-[#1B4F8B] hover:bg-[#F0F5FA] transition-colors duration-100">
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
                  ? 'text-[#0F172A] border-[#1B4F8B]'
                  : 'text-slate-500 hover:text-slate-700 border-transparent'
              )}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={cn(
                  'ml-2 text-[10px] px-1.5 py-0.5 rounded-full font-tabular',
                  tab.key === 'alertes' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'
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

          <div className="space-y-3">
            {filteredAlerts.map((alert) => (
              <div
                key={alert.id}
                className={cn(
                  "bg-white border rounded-lg p-5 transition-all duration-150",
                  alert.severity === 'critical' && alert.status !== 'resolved'
                    ? 'border-red-200/80 bg-red-50/20 hover:bg-red-50/40'
                    : alert.severity === 'warning' && alert.status !== 'resolved'
                    ? 'border-amber-200/60 bg-amber-50/15 hover:bg-amber-50/30'
                    : 'border-slate-200 hover:bg-slate-50/50'
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
                        <span className="text-[10px] font-bold bg-[#1B4F8B]/10 px-2 py-0.5 rounded text-[#1B4F8B] uppercase tracking-wider">
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
                          className="px-3 py-1 bg-[#1B4F8B] text-white text-[11px] font-semibold rounded-md hover:bg-[#153d6e] transition-colors duration-150 shadow-sm"
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
              <div className="text-center py-20 bg-white rounded-lg border border-slate-200">
                <CheckCircle2 size={32} className="mx-auto text-emerald-500 mb-3" />
                <p className="text-slate-600 font-medium text-sm">Zone sécurisée. Aucune alerte système.</p>
              </div>
            )}
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

          {/* Timeline Feed */}
          <div className="relative">
            {/* Vertical timeline line */}
            <div className="absolute left-[39px] top-0 bottom-0 w-px bg-slate-200" />

            {signalementsMock.map((sig, idx) => (
              <div key={sig.id} className={cn(
                "relative p-6 hover:bg-slate-50/50 transition-colors duration-150",
                idx !== signalementsMock.length - 1 && "border-b border-slate-100"
              )}>
                <div className="flex items-start gap-4">
                  {/* Timeline node */}
                  <div className={cn(
                    "relative z-10 w-10 h-10 rounded-full flex items-center justify-center shrink-0 border-2",
                    sig.status === 'Nouveau'
                      ? 'bg-red-50 border-red-200'
                      : sig.status === 'En traitement'
                      ? 'bg-amber-50 border-amber-200'
                      : 'bg-slate-50 border-slate-200'
                  )}>
                    <MessageSquare size={15} className={cn(
                      sig.status === 'Nouveau' ? 'text-red-500' :
                      sig.status === 'En traitement' ? 'text-amber-500' :
                      'text-slate-400'
                    )} />
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex justify-between items-start">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <span className="text-[13px] font-semibold text-[#0F172A]">{sig.author}</span>
                        <span className="text-[11px] text-slate-400 px-1.5 border border-slate-200 rounded">{sig.role}</span>
                        <span className="flex items-center gap-1 text-[11px] font-medium text-[#1B4F8B]">
                          <MapPin size={10} /> {sig.institution}
                        </span>
                      </div>
                      <span className="text-[11px] text-slate-400 shrink-0 ml-3">{sig.timestamp}</span>
                    </div>
                    <p className="text-[13px] text-slate-600 leading-relaxed max-w-3xl mt-1">{sig.issue}</p>
                    
                    <div className="flex items-center gap-3 mt-4">
                      <span className={cn(
                        "text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded",
                        sig.status === 'Nouveau' ? "bg-red-50 text-red-600 border border-red-100" :
                        sig.status === 'En traitement' ? "bg-amber-50 text-amber-600 border border-amber-100" :
                        "bg-emerald-50 text-emerald-600 border border-emerald-100"
                      )}>
                        {sig.status}
                      </span>
                      {sig.status !== 'Résolu' && (
                        <button className="text-[11px] font-semibold text-[#1B4F8B] hover:underline">
                          Assigner un technicien →
                        </button>
                      )}
                      <span className="text-[10px] text-slate-300 uppercase tracking-wider ml-auto">{sig.id}</span>
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
