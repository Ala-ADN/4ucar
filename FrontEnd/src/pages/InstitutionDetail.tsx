import { useParams, Link } from "react-router-dom";
import { motion, AnimatePresence } from "motion/react";
import { 
  ArrowLeft, 
  MapPin, 
  Users, 
  GraduationCap, 
  Wallet, 
  FlaskConical, 
  Building2, 
  UserRoundCheck,
  TrendingUp,
  TrendingDown,
  FileText,
  Trophy,
  AlertCircle
} from "lucide-react";
import { useState } from "react";
import { Institution, HealthStatus } from "@/src/types";
import institutionsData from "@/src/data/institutions.json";
import { Badge, StatusDot } from "@/src/components/ui/StatusDot";
import { KPICard } from "@/src/components/kpi/KPICard";
import { cn } from "@/src/lib/utils";
import { 
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';

const tabs = [
  { id: 'academic', label: 'Académique', icon: GraduationCap },
  { id: 'financial', label: 'Financier', icon: Wallet },
  { id: 'hr', label: 'RH', icon: UserRoundCheck },
  { id: 'research', label: 'Recherche', icon: FlaskConical },
  { id: 'infra', label: 'Infrastructure', icon: Building2 },
];

const COLORS = ['#3B82F6', '#6366F1', '#A855F7', '#EC4899'];

export function InstitutionDetail() {
  const { code } = useParams();
  const [activeTab, setActiveTab] = useState('academic');
  
  const institution = (institutionsData as Institution[]).find(i => i.code === code);

  if (!institution) return <div>Établissement non trouvé</div>;

  return (
    <div className="space-y-8">
      {/* Breadcrumbs */}
      <div className="flex items-center gap-2 text-xs font-medium text-text-muted">
        <span>UCAR</span>
        <span className="text-border-strong">/</span>
        <Link to="/institutions" className="hover:text-blue-500 transition-colors">Établissements</Link>
        <span className="text-border-strong">/</span>
        <span className="text-text-primary font-bold">{institution.code}</span>
      </div>

      {/* Header */}
      <div className="bg-white p-10 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden">
        {/* Decorative Grid Accent */}
        <div className="absolute top-0 right-0 w-96 h-96 bg-slate-50 border-l border-b border-slate-100 -mr-20 -mt-20 opacity-40 pointer-events-none transform rotate-12" />
        
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-10 relative">
          <div className="flex items-center gap-8">
            <div className="w-24 h-24 rounded-2xl bg-blue-600 flex items-center justify-center text-white text-4xl font-bold uppercase shadow-xl shadow-blue-500/20">
              {institution.code.substring(0, 2)}
            </div>
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="text-4xl font-bold tracking-tight text-slate-900">{institution.code}</h1>
                <Badge variant={institution.type === 'grande_ecole' ? 'info' : (institution.type === 'faculte' ? 'purple' : 'amber')}>
                  {institution.type.replace('_', ' ')}
                </Badge>
                <div className="flex items-center gap-1.5 ml-2">
                   <div className="w-2 h-2 rounded-full bg-blue-600 shadow-[0_0_8px_rgba(37,99,235,0.6)]" />
                   <span className="text-[10px] font-bold text-blue-600 uppercase tracking-widest">Actif</span>
                </div>
              </div>
              <p className="text-slate-500 text-lg font-medium">{institution.name}</p>
              <div className="flex items-center gap-6 mt-6 text-xs text-slate-400 font-bold uppercase tracking-widest">
                <span className="flex items-center gap-2"><MapPin size={14} className="text-blue-600" /> {institution.city}</span>
                <span className="flex items-center gap-2"><Users size={14} className="text-blue-600" /> {institution.students.toLocaleString()} ÉTUDIANTS</span>
                <span className="flex items-center gap-2"><div className="w-1.5 h-1.5 rounded-full bg-slate-200" /> RÉSEAU TUNISIEN</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-6 min-w-[240px]">
            <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 grid grid-cols-4 gap-4">
              <HealthDot label="Acad." status={institution.health.academic} />
              <HealthDot label="Fin." status={institution.health.financial} />
              <HealthDot label="RH" status={institution.health.hr} />
              <HealthDot label="Rech." status={institution.health.research} />
            </div>
            <Link 
              to="/institutions"
              className="flex items-center justify-center gap-3 px-6 py-3 bg-slate-900 text-white rounded-xl text-[11px] font-bold uppercase tracking-widest hover:bg-slate-800 transition-all shadow-lg shadow-black/10"
            >
              <ArrowLeft size={16} /> Retour au Portail
            </Link>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1.5 bg-slate-900 p-2 rounded-2xl shadow-xl shadow-slate-900/10 w-fit max-w-full overflow-x-auto">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "flex items-center gap-2 px-6 py-3 rounded-xl text-[11px] font-bold uppercase tracking-widest transition-all whitespace-nowrap",
              activeTab === tab.id 
                ? "bg-blue-600 text-white shadow-lg shadow-blue-600/20" 
                : "text-slate-400 hover:text-white"
            )}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, x: 10 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -10 }}
          transition={{ duration: 0.3 }}
        >
          {activeTab === 'academic' && <AcademicTab institution={institution} />}
          {activeTab === 'financial' && <FinancialTab institution={institution} />}
          {activeTab === 'hr' && <HRTab institution={institution} />}
          {activeTab === 'research' && <ResearchTab institution={institution} />}
          {activeTab === 'infra' && <InfraTab institution={institution} />}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

function HealthDot({ label, status }: { label: string, status: HealthStatus }) {
  const colors = {
    good: "bg-green-500",
    warning: "bg-amber-500",
    critical: "bg-red-500"
  };
  return (
    <div className="flex flex-col items-center gap-2">
      <div className={cn("w-2 h-2 rounded-full", colors[status])} />
      <span className="text-[8px] font-black text-slate-300 uppercase tracking-tighter">{label}</span>
    </div>
  );
}

// --- TAB CONTENT COMPONENTS ---

function AcademicTab({ institution }: { institution: Institution }) {
  const data = [
    { name: 'S1 22', rate: 71 },
    { name: 'S2 22', rate: 74 },
    { name: 'S1 23', rate: 72 },
    { name: 'S2 23', rate: 76 },
    { name: 'S1 24', rate: 75 },
    { name: 'S2 24', rate: (institution.kpi_snapshot?.taux_reussite ?? 0) },
  ];

  const programData = [
    { name: 'Info.', success: 82, failures: 12 },
    { name: 'Telecom', success: 75, failures: 18 },
    { name: 'Bio.', success: 68, failures: 24 },
    { name: 'Indus.', success: 71, failures: 21 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Taux de réussite" value={institution.kpi_snapshot?.taux_reussite ?? 0} suffix="%" icon={TrendingUp} trend={{ value: 2.1, unit: '%' }} />
        <KPICard label="Taux d'abandon" value={institution.kpi_snapshot?.taux_abandon ?? 0} suffix="%" icon={Users} trend={{ value: -0.4, unit: '%', isPositiveGood: false }} />
        <KPICard label="Redoublement" value={institution.kpi_snapshot?.taux_redoublement ?? 0} suffix="%" icon={FileText} trend={{ value: 0, unit: '%' }} />
        <KPICard label="Mention TB" value={18.7} suffix="%" icon={Trophy} trend={{ value: 1.2, unit: '%' }} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-surface p-6 rounded-2xl shadow-card">
          <h3 className="text-base font-bold text-text-primary mb-6">Évolution de la réussite</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <defs>
                  <linearGradient id="colorRate" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10 }} unit="%" />
                <Tooltip contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 16px rgba(0,0,0,0.08)' }} />
                <Area type="monotone" dataKey="rate" stroke="#3B82F6" strokeWidth={3} fillOpacity={1} fill="url(#colorRate)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-surface p-6 rounded-2xl shadow-card">
          <h3 className="text-base font-bold text-text-primary mb-6">Performance par filière</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={programData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10 }} unit="%" />
                <Tooltip cursor={{ fill: 'transparent' }} contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 8px 16px rgba(0,0,0,0.08)' }} />
                <Bar dataKey="success" name="Réussite" fill="#3B82F6" radius={[4, 4, 0, 0]} barSize={24} />
                <Bar dataKey="failures" name="Échec" fill="#EF4444" radius={[4, 4, 0, 0]} barSize={24} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}

function FinancialTab({ institution }: { institution: Institution }) {
  const budgetData = [
    { name: 'Chap. 1', alloue: 1800, engage: 1400, paye: 1200 },
    { name: 'Chap. 2', alloue: 600, engage: 400, paye: 350 },
    { name: 'Chap. 3', alloue: 300, engage: 280, paye: 210 },
    { name: 'Chap. 4', alloue: 150, engage: 120, paye: 100 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Budget alloué" value="2 850" suffix="k TND" icon={Wallet} />
        <KPICard label="Taux d'exécution" value={institution.kpi_snapshot?.budget_execution ?? 0} suffix="%" icon={TrendingUp} />
        <KPICard label="Masse salariale" value={institution.kpi_snapshot?.masse_salariale_pct ?? 0} suffix="%" icon={Users} />
        <KPICard label="Projection fin d'année" value={91} suffix="%" icon={TrendingUp} />
      </div>

      <div className="bg-surface p-8 rounded-2xl shadow-card border border-border">
        <h3 className="text-base font-bold text-text-primary mb-8">Structure de l'exécution budgétaire</h3>
        
        <BudgetProgress 
          paye={institution.kpi_snapshot?.budget_execution ?? 0} 
          engage={15} 
          mandate={10} 
        />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mt-12">
          <div className="space-y-4">
            <h4 className="text-xs font-bold text-text-muted uppercase tracking-widest">Détail par chapitre</h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={budgetData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} />
                  <Tooltip cursor={{ fill: '#F1F5F9' }} />
                  <Bar dataKey="alloue" name="Alloué" fill="#E2E8F0" radius={[0, 4, 4, 0]} barSize={20} />
                  <Bar dataKey="paye" name="Payé" fill="#3B82F6" radius={[0, 4, 4, 0]} barSize={20} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
          
          <div className="bg-blue-50/50 p-6 rounded-2xl border border-blue-100 h-fit">
            <h4 className="text-sm font-bold text-blue-900 mb-4">Observation analytique</h4>
            <p className="text-sm text-blue-800 leading-relaxed">
              L'exécution budgétaire est en phase avec les objectifs du trimestre, à l'exception du Chapitre 2 (Investissement) qui accuse un retard de facturation sur les équipements de laboratoire. Une régularisation est attendue en S2.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function BudgetProgress({ paye, engage, mandate }: { paye: number, engage: number, mandate: number }) {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end">
        <div className="space-y-1">
          <span className="text-4xl font-serif font-bold text-text-primary">{paye}%</span>
          <p className="text-xs text-text-muted font-bold uppercase tracking-wider">Payé à ce jour</p>
        </div>
        <div className="text-right">
          <span className="text-lg font-bold text-text-secondary">{100-paye}%</span>
          <p className="text-[10px] text-text-muted font-bold uppercase tracking-wider">Solde restant</p>
        </div>
      </div>
      <div className="h-5 w-full bg-off-white rounded-full overflow-hidden flex shadow-inner">
        <motion.div initial={{ width: 0 }} animate={{ width: `${paye}%` }} transition={{ duration: 1 }} className="h-full bg-blue-600" />
        <motion.div initial={{ width: 0 }} animate={{ width: `${mandate}%` }} transition={{ duration: 1, delay: 0.2 }} className="h-full bg-blue-400" />
        <motion.div initial={{ width: 0 }} animate={{ width: `${engage}%` }} transition={{ duration: 1, delay: 0.4 }} className="h-full bg-blue-200" />
      </div>
      <div className="flex flex-wrap gap-6 pt-2">
        <LegendItem2 color="bg-blue-600" label="Payé" value={`${paye}%`} />
        <LegendItem2 color="bg-blue-400" label="Mandaté" value={`${mandate}%`} />
        <LegendItem2 color="bg-blue-200" label="Engagé" value={`${engage}%`} />
        <LegendItem2 color="bg-off-white" label="Solde" value={`${100 - (paye+mandate+engage)}%`} />
      </div>
    </div>
  );
}

function LegendItem2({ color, label, value }: { color: string, label: string, value: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={cn("w-3 h-3 rounded-[3px]", color)} />
      <span className="text-[11px] font-bold text-text-secondary">{label}:</span>
      <span className="text-[11px] font-black text-text-primary">{value}</span>
    </div>
  );
}

function HRTab({ institution }: { institution: Institution }) {
  const staffData = [
    { name: 'Corps A', value: 48 },
    { name: 'Corps B', value: 124 },
    { name: 'Admin', value: 85 },
    { name: 'Vacataires', value: 55 },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Effectif total" value={312} icon={Users} />
        <KPICard label="Taux d'encadrement" value={`1 / ${institution.kpi_snapshot?.taux_encadrement ?? 0}`} icon={UserRoundCheck} />
        <KPICard label="Absentéisme" value={institution.kpi_snapshot?.taux_absenteisme ?? 0} suffix="%" icon={TrendingDown} trend={{ value: 0.5, unit: '%', isPositiveGood: false }} />
        <KPICard label="Taux vacataires" value={institution.kpi_snapshot?.taux_vacataires ?? 0} suffix="%" icon={Users} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 bg-surface p-6 rounded-2xl shadow-card">
          <h3 className="text-base font-bold text-text-primary mb-8">Répartition du personnel</h3>
          <div className="h-64 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={staffData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {staffData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-serif font-bold text-text-primary">312</span>
              <span className="text-[10px] font-bold text-text-muted uppercase">Total</span>
            </div>
          </div>
          <div className="space-y-3 mt-4">
            {staffData.map((item, idx) => (
              <div key={item.name} className="flex justify-between items-center text-[11px] font-bold">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                  <span className="text-text-secondary">{item.name}</span>
                </div>
                <span className="text-text-primary">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-8 bg-surface p-6 rounded-2xl shadow-card">
          <h3 className="text-base font-bold text-text-primary mb-8">Charge d'enseignement (ETD)</h3>
          <div className="space-y-6">
            <LoadBar label="Corps A" value={210} max={250} />
            <LoadBar label="Corps B" value={285} max={250} />
            <LoadBar label="Vacataires" value={140} max={250} />
          </div>
          <div className="mt-12 bg-status-info-bg p-4 rounded-xl border border-blue-100 flex items-start gap-4">
            <div className="p-2 bg-blue-500 rounded-lg text-white">
              <AlertCircle size={18} />
            </div>
            <div>
              <h4 className="text-sm font-bold text-blue-900">Alerte surcharge</h4>
              <p className="text-xs text-blue-800 mt-1">Le Corps B présente une surcharge moyenne de 14% par rapport au référentiel ETD normal. Un appel à vacataires supplémentaire est en cours d'approbation.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadBar({ label, value, max }: { label: string, value: number, max: number }) {
  const percentage = Math.min((value / max) * 100, 100);
  const isOverloaded = value > max;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-xs font-bold">
        <span className="text-text-secondary">{label}</span>
        <span className={cn(isOverloaded ? "text-status-critical" : "text-text-primary")}>
          {value} ETD {isOverloaded && "(Surcharge)"}
        </span>
      </div>
      <div className="h-2 w-full bg-off-white rounded-full overflow-hidden">
        <motion.div 
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          className={cn("h-full rounded-full", isOverloaded ? "bg-status-critical" : "bg-status-good")}
        />
      </div>
    </div>
  );
}

function ResearchTab({ institution }: { institution: Institution }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Publications indexées" value={institution.kpi_snapshot?.publications_indexees ?? 0} suffix=" / an" icon={FileText} />
        <KPICard label="Thèses actives" value={institution.kpi_snapshot?.theses_actives ?? 0} icon={GraduationCap} />
        <KPICard label="Financements (TND)" value="320k" icon={Wallet} />
        <KPICard label="Laboratoires" value={8} icon={FlaskConical} />
      </div>
      <div className="bg-surface p-12 rounded-2xl shadow-card text-center border border-dashed border-border">
        <FlaskConical size={48} className="mx-auto text-text-muted mb-4 opacity-20" />
        <p className="text-sm text-text-muted">Visualisation des réseaux de recherche en cours de déploiement...</p>
      </div>
    </div>
  );
}

function InfraTab({ institution }: { institution: Institution }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-surface p-8 rounded-2xl shadow-card text-center">
        <KPICard label="Taux d'occupation" value={institution.kpi_snapshot?.room_occupancy ?? 0} suffix="%" icon={Building2} />
        <div className="mt-8 text-sm text-text-secondary leading-relaxed">
          Occupation optimale des salles de cours et amphithéâtres. Les créneaux du soir (18h-20h) sont disponibles pour la formation continue.
        </div>
      </div>
      <div className="bg-surface p-8 rounded-2xl shadow-card flex flex-col justify-center items-center gap-12 border border-border">
        <div className="w-48 h-48 rounded-full border-8 border-status-good flex flex-col items-center justify-center p-2">
            <span className="text-4xl font-serif font-black text-text-primary">94%</span>
            <span className="text-[10px] font-bold text-text-muted uppercase text-center">Équipements opérationnels</span>
        </div>
      </div>
    </div>
  );
}
