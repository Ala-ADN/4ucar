import { useParams, Link } from 'react-router-dom';
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
  AlertCircle,
} from 'lucide-react';
import { useState } from 'react';
import { Institution, HealthStatus } from '@/src/types';
import institutionsData from '@/src/data/institutions.json';
import { Badge } from '@/src/components/ui/StatusDot';
import { KPICard } from '@/src/components/kpi/KPICard';
import { cn } from '@/src/lib/utils';
import {
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';

const tabs = [
  { id: 'academic', label: 'Academique', icon: GraduationCap },
  { id: 'financial', label: 'Financier', icon: Wallet },
  { id: 'hr', label: 'RH', icon: UserRoundCheck },
  { id: 'research', label: 'Recherche', icon: FlaskConical },
  { id: 'infra', label: 'Infrastructure', icon: Building2 },
] as const;

const COLORS = ['#1d4ed8', '#334155', '#0f766e', '#b45309'];

type TabId = (typeof tabs)[number]['id'];

export function InstitutionDetail() {
  const { code } = useParams();
  const [activeTab, setActiveTab] = useState<TabId>('academic');

  const institution = (institutionsData as Institution[]).find((i) => i.code === code);

  if (!institution) {
    return <div className="text-sm text-slate-700">Etablissement non trouve</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <span>UCAR</span>
        <span>/</span>
        <Link to="/institutions" className="hover:text-blue-800 transition-colors duration-150">
          Etablissements
        </Link>
        <span>/</span>
        <span className="text-slate-900 font-medium">{institution.code}</span>
      </div>

      <div className="bg-white p-6 rounded-md border border-slate-200">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="flex items-start gap-5">
            <div className="w-16 h-16 rounded-md bg-blue-800 flex items-center justify-center text-white text-xl font-semibold uppercase">
              {institution.code.substring(0, 2)}
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h1 className="text-2xl font-semibold text-slate-900">{institution.code}</h1>
                <Badge variant={institution.type === 'grande_ecole' ? 'info' : institution.type === 'faculte' ? 'purple' : 'amber'}>
                  {institution.type.replace('_', ' ')}
                </Badge>
                <span className="text-xs text-green-700 bg-green-50 border border-green-200 rounded px-2 py-0.5">Actif</span>
              </div>
              <p className="text-slate-700 text-base font-medium">{institution.name}</p>
              <div className="flex flex-wrap items-center gap-5 mt-4 text-sm text-slate-600">
                <span className="flex items-center gap-2">
                  <MapPin size={14} /> {institution.city}
                </span>
                <span className="flex items-center gap-2">
                  <Users size={14} /> {institution.students.toLocaleString()} etudiants
                </span>
                <span>Reseau tunisien</span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 min-w-[240px]">
            <div className="bg-slate-50 p-3 rounded border border-slate-200 grid grid-cols-4 gap-2">
              <HealthDot label="Acad." status={institution.health.academic} />
              <HealthDot label="Fin." status={institution.health.financial} />
              <HealthDot label="RH" status={institution.health.hr} />
              <HealthDot label="Rech." status={institution.health.research} />
            </div>
            <Link
              to="/institutions"
              className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-800 text-white rounded-md text-sm font-medium hover:bg-blue-900 transition-colors duration-150"
            >
              <ArrowLeft size={16} /> Retour au portail
            </Link>
          </div>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 bg-white p-2 rounded-md border border-slate-200">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              'flex items-center gap-2 px-3 py-1.5 rounded text-sm font-medium transition-colors duration-150',
              activeTab === tab.id ? 'bg-blue-800 text-white' : 'text-slate-700 hover:bg-slate-100'
            )}
          >
            <tab.icon size={16} />
            {tab.label}
          </button>
        ))}
      </div>

      {activeTab === 'academic' && <AcademicTab institution={institution} />}
      {activeTab === 'financial' && <FinancialTab institution={institution} />}
      {activeTab === 'hr' && <HRTab institution={institution} />}
      {activeTab === 'research' && <ResearchTab institution={institution} />}
      {activeTab === 'infra' && <InfraTab institution={institution} />}
    </div>
  );
}

function HealthDot({ label, status }: { label: string; status: HealthStatus }) {
  const colors = {
    good: 'bg-green-600',
    warning: 'bg-amber-500',
    critical: 'bg-red-600',
  };

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div className={cn('w-2.5 h-2.5 rounded-full', colors[status])} />
      <span className="text-[10px] font-medium text-slate-500">{label}</span>
    </div>
  );
}

function AcademicTab({ institution }: { institution: Institution }) {
  const data = [
    { name: 'S1 22', rate: 71 },
    { name: 'S2 22', rate: 74 },
    { name: 'S1 23', rate: 72 },
    { name: 'S2 23', rate: 76 },
    { name: 'S1 24', rate: 75 },
    { name: 'S2 24', rate: institution.kpi_snapshot?.taux_reussite ?? 0 },
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
        <KPICard label="Taux de reussite" value={institution.kpi_snapshot?.taux_reussite ?? 0} suffix="%" icon={TrendingUp} trend={{ value: 2.1, unit: '%' }} />
        <KPICard label="Taux d'abandon" value={institution.kpi_snapshot?.taux_abandon ?? 0} suffix="%" icon={Users} trend={{ value: -0.4, unit: '%', isPositiveGood: false }} />
        <KPICard label="Redoublement" value={institution.kpi_snapshot?.taux_redoublement ?? 0} suffix="%" icon={FileText} trend={{ value: 0, unit: '%' }} />
        <KPICard label="Mention TB" value={18.7} suffix="%" icon={Trophy} trend={{ value: 1.2, unit: '%' }} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Evolution de la reussite</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={data}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Area type="monotone" dataKey="rate" stroke="#1d4ed8" strokeWidth={2} fill="#bfdbfe" fillOpacity={0.4} />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Performance par filiere</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={programData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Bar dataKey="success" name="Reussite" fill="#1d4ed8" radius={[2, 2, 0, 0]} barSize={20} />
                <Bar dataKey="failures" name="Echec" fill="#dc2626" radius={[2, 2, 0, 0]} barSize={20} />
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
        <KPICard label="Budget alloue" value="2 850" suffix="k TND" icon={Wallet} />
        <KPICard label="Taux d'execution" value={institution.kpi_snapshot?.budget_execution ?? 0} suffix="%" icon={TrendingUp} />
        <KPICard label="Masse salariale" value={institution.kpi_snapshot?.masse_salariale_pct ?? 0} suffix="%" icon={Users} />
        <KPICard label="Projection fin d'annee" value={91} suffix="%" icon={TrendingUp} />
      </div>

      <div className="bg-white p-6 rounded-md border border-slate-200">
        <h3 className="text-base font-semibold text-slate-900 mb-6">Structure de l'execution budgetaire</h3>

        <BudgetProgress paye={institution.kpi_snapshot?.budget_execution ?? 0} engage={15} mandate={10} />

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
          <div className="space-y-4">
            <h4 className="text-sm font-medium text-slate-700">Detail par chapitre</h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={budgetData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} />
                  <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                  <Bar dataKey="alloue" name="Alloue" fill="#cbd5e1" radius={[0, 2, 2, 0]} barSize={16} />
                  <Bar dataKey="paye" name="Paye" fill="#1d4ed8" radius={[0, 2, 2, 0]} barSize={16} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-slate-50 p-5 rounded-md border border-slate-200 h-fit">
            <h4 className="text-sm font-semibold text-slate-900 mb-3">Observation analytique</h4>
            <p className="text-sm text-slate-700 leading-relaxed">
              L'execution budgetaire est en phase avec les objectifs du trimestre, a l'exception du Chapitre 2 (Investissement)
              qui accuse un retard de facturation sur les equipements de laboratoire. Une regularisation est attendue en S2.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function BudgetProgress({ paye, engage, mandate }: { paye: number; engage: number; mandate: number }) {
  const payeWidth = Math.max(0, Math.min(paye, 100));
  const mandateWidth = Math.max(0, Math.min(mandate, 100 - payeWidth));
  const engageWidth = Math.max(0, Math.min(engage, 100 - payeWidth - mandateWidth));

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-end">
        <div className="space-y-1">
          <span className="text-3xl font-semibold text-slate-900">{paye}%</span>
          <p className="text-xs text-slate-600">Paye a ce jour</p>
        </div>
        <div className="text-right">
          <span className="text-lg font-semibold text-slate-800">{100 - paye}%</span>
          <p className="text-xs text-slate-600">Solde restant</p>
        </div>
      </div>
      <div className="h-4 w-full bg-slate-100 rounded-full overflow-hidden flex">
        <div className="h-full bg-blue-700" style={{ width: `${payeWidth}%` }} />
        <div className="h-full bg-blue-400" style={{ width: `${mandateWidth}%` }} />
        <div className="h-full bg-blue-200" style={{ width: `${engageWidth}%` }} />
      </div>
      <div className="flex flex-wrap gap-4 pt-1">
        <LegendItem2 color="bg-blue-700" label="Paye" value={`${paye}%`} />
        <LegendItem2 color="bg-blue-400" label="Mandate" value={`${mandate}%`} />
        <LegendItem2 color="bg-blue-200" label="Engage" value={`${engage}%`} />
        <LegendItem2 color="bg-slate-100" label="Solde" value={`${Math.max(0, 100 - (paye + mandate + engage))}%`} />
      </div>
    </div>
  );
}

function LegendItem2({ color, label, value }: { color: string; label: string; value: string }) {
  return (
    <div className="flex items-center gap-2">
      <div className={cn('w-3 h-3 rounded-[3px] border border-slate-300', color)} />
      <span className="text-xs text-slate-700">{label}:</span>
      <span className="text-xs font-semibold text-slate-900">{value}</span>
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
        <KPICard label="Absenteisme" value={institution.kpi_snapshot?.taux_absenteisme ?? 0} suffix="%" icon={TrendingDown} trend={{ value: 0.5, unit: '%', isPositiveGood: false }} />
        <KPICard label="Taux vacataires" value={institution.kpi_snapshot?.taux_vacataires ?? 0} suffix="%" icon={Users} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-4 bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-5">Repartition du personnel</h3>
          <div className="h-64 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={staffData} cx="50%" cy="50%" innerRadius={55} outerRadius={75} paddingAngle={2} dataKey="value">
                  {staffData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <span className="text-2xl font-semibold text-slate-900">312</span>
              <span className="text-xs text-slate-600">Total</span>
            </div>
          </div>
          <div className="space-y-2 mt-4">
            {staffData.map((item, idx) => (
              <div key={item.name} className="flex justify-between items-center text-xs">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: COLORS[idx] }} />
                  <span className="text-slate-700">{item.name}</span>
                </div>
                <span className="text-slate-900 font-medium">{item.value}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="lg:col-span-8 bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-6">Charge d'enseignement (ETD)</h3>
          <div className="space-y-5">
            <LoadBar label="Corps A" value={210} max={250} />
            <LoadBar label="Corps B" value={285} max={250} />
            <LoadBar label="Vacataires" value={140} max={250} />
          </div>
          <div className="mt-8 bg-red-50 p-4 rounded-md border border-red-200 flex items-start gap-3">
            <div className="p-2 bg-red-600 rounded text-white">
              <AlertCircle size={16} />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-red-800">Alerte surcharge</h4>
              <p className="text-sm text-red-700 mt-1">
                Le Corps B presente une surcharge moyenne de 14% par rapport au referentiel ETD normal.
                Un appel a vacataires supplementaire est en cours d'approbation.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function LoadBar({ label, value, max }: { label: string; value: number; max: number }) {
  const percentage = Math.min((value / max) * 100, 100);
  const isOverloaded = value > max;

  return (
    <div className="space-y-2">
      <div className="flex justify-between text-sm">
        <span className="text-slate-700">{label}</span>
        <span className={cn(isOverloaded ? 'text-red-700 font-medium' : 'text-slate-900 font-medium')}>
          {value} ETD {isOverloaded && '(Surcharge)'}
        </span>
      </div>
      <div className="h-2.5 w-full bg-slate-100 rounded-full overflow-hidden">
        <div className={cn('h-full rounded-full', isOverloaded ? 'bg-red-600' : 'bg-green-700')} style={{ width: `${percentage}%` }} />
      </div>
    </div>
  );
}

function ResearchTab({ institution }: { institution: Institution }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Publications indexees" value={institution.kpi_snapshot?.publications_indexees ?? 0} suffix=" / an" icon={FileText} />
        <KPICard label="Theses actives" value={institution.kpi_snapshot?.theses_actives ?? 0} icon={GraduationCap} />
        <KPICard label="Financements (TND)" value="320k" icon={Wallet} />
        <KPICard label="Laboratoires" value={8} icon={FlaskConical} />
      </div>
      <div className="bg-white p-10 rounded-md border border-slate-200 text-center">
        <FlaskConical size={40} className="mx-auto text-slate-400 mb-4" />
        <p className="text-sm text-slate-600">Visualisation des reseaux de recherche en cours de deploiement.</p>
      </div>
    </div>
  );
}

function InfraTab({ institution }: { institution: Institution }) {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="bg-white p-6 rounded-md border border-slate-200 text-center">
        <KPICard label="Taux d'occupation" value={institution.kpi_snapshot?.room_occupancy ?? 0} suffix="%" icon={Building2} />
        <div className="mt-6 text-sm text-slate-700 leading-relaxed">
          Occupation optimale des salles de cours et amphitheatres. Les creneaux du soir (18h-20h)
          sont disponibles pour la formation continue.
        </div>
      </div>
      <div className="bg-white p-6 rounded-md border border-slate-200 flex flex-col justify-center items-center gap-6">
        <div className="w-40 h-40 rounded-full border-8 border-green-700 flex flex-col items-center justify-center p-2">
          <span className="text-3xl font-semibold text-slate-900">94%</span>
          <span className="text-xs text-slate-600 text-center">Equipements operationnels</span>
        </div>
      </div>
    </div>
  );
}
