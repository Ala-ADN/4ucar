import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Users,
  GraduationCap,
  Leaf,
  ShieldCheck,
  UserRoundCheck,
  TrendingUp,
  TrendingDown,
  AlertCircle,
} from 'lucide-react';
import { useState, useMemo } from 'react';
import { DashboardInstitution, HealthStatus } from '@/src/types';
import { institutions, institutionKpiSeries, alerts as allAlerts } from '@/src/data/dashboardMock';
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
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
} from 'recharts';

const tabs = [
  { id: 'academic', label: 'Académique', icon: GraduationCap },
  { id: 'sustainability', label: 'Durabilité', icon: Leaf },
  { id: 'governance', label: 'Gouvernance', icon: ShieldCheck },
  { id: 'hr', label: 'RH', icon: UserRoundCheck },
  { id: 'accreditation', label: 'Accréditation', icon: ShieldCheck },
] as const;

type TabId = (typeof tabs)[number]['id'];

export function InstitutionDetail() {
  const { code } = useParams();
  const [activeTab, setActiveTab] = useState<TabId>('academic');

  const institution = institutions.find((i) => i.code === code);

  const ucarMedian = useMemo(() => {
    const scores: Record<string, number> = {};
    const keys = ['successRate', 'dropoutRate', 'curriculumCoverage', 'workloadCompliance', 'documentControlCompliance', 'auditNCRClosureRate', 'energyPerStudent', 'renewableEnergyRate', 'recyclingRate', 'genderDiversityIndex'] as const;
    keys.forEach(k => {
      const values = institutions.map(i => i.kpiSnapshot[k]);
      scores[k] = Number((values.reduce((a, b) => a + b, 0) / values.length).toFixed(1));
    });
    return scores;
  }, []);

  const ucarBest = useMemo(() => {
    const scores: Record<string, number> = {};
    const maxKeys = ['successRate', 'curriculumCoverage', 'workloadCompliance', 'documentControlCompliance', 'auditNCRClosureRate', 'renewableEnergyRate', 'recyclingRate', 'genderDiversityIndex'] as const;
    maxKeys.forEach(k => {
      scores[k] = Math.max(...institutions.map(i => i.kpiSnapshot[k]));
    });
    // Lower is better
    scores['dropoutRate'] = Math.min(...institutions.map(i => i.kpiSnapshot.dropoutRate));
    scores['energyPerStudent'] = Math.min(...institutions.map(i => i.kpiSnapshot.energyPerStudent));
    scores['studentFacultyRatio'] = Math.min(...institutions.map(i => i.kpiSnapshot.studentFacultyRatio));
    return scores;
  }, []);

  if (!institution) {
    return <div className="text-sm text-slate-700">Établissement non trouvé</div>;
  }

  const institutionAlerts = allAlerts.filter(a => a.institutionCode === code && a.status !== 'resolved');

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-2 text-sm text-slate-500">
        <span>UCAR</span>
        <span>/</span>
        <Link to="/institutions" className="hover:text-blue-800 transition-colors duration-150">
          Établissements
        </Link>
        <span>/</span>
        <span className="text-slate-900 font-medium">{institution.code}</span>
      </div>

      {/* Header Card with UCAR Score + Rank */}
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
                  <Users size={14} /> {institution.students.toLocaleString()} étudiants
                </span>
              </div>
            </div>
          </div>

          <div className="flex flex-col gap-4 min-w-72">
            {/* UCAR Score + Rank + Delta */}
            <div className="bg-slate-50 p-4 rounded border border-slate-200 flex items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-bold text-slate-900 font-tabular">{institution.ucarScore}</p>
                <p className="text-xs text-slate-500 mt-1">Score UCAR</p>
              </div>
              <div className="h-12 w-px bg-slate-200" />
              <div className="text-center">
                <p className="text-2xl font-bold text-slate-900 font-tabular">#{institution.rank}</p>
                <p className="text-xs text-slate-500 mt-1">Rang / 35</p>
              </div>
              <div className="h-12 w-px bg-slate-200" />
              <div className="text-center">
                <p className={cn('text-xl font-bold font-tabular', institution.scoreDelta >= 0 ? 'text-green-700' : 'text-red-700')}>
                  {institution.scoreDelta >= 0 ? '+' : ''}{institution.scoreDelta}
                </p>
                <p className="text-xs text-slate-500 mt-1">Δ période</p>
              </div>
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

      {/* Domain Radar Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-5 bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Profil radar — domaines KPI</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <RadarChart data={[
                { domain: 'Académique', value: institution.domainScores.academic, median: 75 },
                { domain: 'Durabilité', value: institution.domainScores.sustainability, median: 66 },
                { domain: 'Gouvernance', value: institution.domainScores.governance, median: 76 },
                { domain: 'RH', value: institution.domainScores.hr, median: 73 },
              ]}>
                <PolarGrid stroke="#e2e8f0" />
                <PolarAngleAxis dataKey="domain" tick={{ fontSize: 11, fill: '#475569' }} />
                <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                <Radar name="Institution" dataKey="value" stroke="#2563eb" fill="#2563eb" fillOpacity={0.2} strokeWidth={2} />
                <Radar name="Médiane UCAR" dataKey="median" stroke="#94a3b8" fill="transparent" strokeWidth={1} strokeDasharray="5 5" />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #e2e8f0', boxShadow: 'none', fontSize: '12px' }} />
              </RadarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="lg:col-span-7 bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Alertes institution</h3>
          {institutionAlerts.length === 0 ? (
            <div className="text-center py-10">
              <TrendingUp size={32} className="mx-auto text-green-600 mb-2" />
              <p className="text-sm text-slate-600">Aucune alerte active pour cet établissement.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {institutionAlerts.map(alert => (
                <div key={alert.id} className={cn(
                  'p-3 rounded-md border flex items-start gap-3',
                  alert.severity === 'critical' ? 'bg-red-50 border-red-200' : 'bg-amber-50 border-amber-200'
                )}>
                  <AlertCircle size={16} className={alert.severity === 'critical' ? 'text-red-600 mt-0.5' : 'text-amber-600 mt-0.5'} />
                  <div>
                    <p className="text-sm font-medium text-slate-900">{alert.title}</p>
                    <p className="text-xs text-slate-600 mt-1">{alert.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Tabs */}
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

      {activeTab === 'academic' && <AcademicTab institution={institution} ucarMedian={ucarMedian} ucarBest={ucarBest} />}
      {activeTab === 'sustainability' && <SustainabilityTab institution={institution} ucarMedian={ucarMedian} ucarBest={ucarBest} />}
      {activeTab === 'governance' && <GovernanceTab institution={institution} ucarMedian={ucarMedian} ucarBest={ucarBest} />}
      {activeTab === 'hr' && <HRTab institution={institution} ucarMedian={ucarMedian} ucarBest={ucarBest} />}
      {activeTab === 'accreditation' && <AccreditationTab institution={institution} />}
    </div>
  );
}

function KPIStatus({ value, thresholds }: { value: number; thresholds: { green: number; amber: number }; }) {
  const status = value >= thresholds.green ? 'good' : value >= thresholds.amber ? 'warning' : 'critical';
  const colors = { good: 'bg-green-600', warning: 'bg-amber-500', critical: 'bg-red-600' };
  return <div className={cn('w-2.5 h-2.5 rounded-full inline-block', colors[status])} />;
}

function ComparisonRow({ label, kpiId, value, median, best, unit = '%', lowerBetter = false }: {
  label: string; kpiId: string; value: number; median: number; best: number; unit?: string; lowerBetter?: boolean;
}) {
  const isGood = lowerBetter ? value <= median : value >= median;
  return (
    <tr className="hover:bg-slate-50">
      <td className="px-4 py-2.5 text-sm text-slate-700">{label} <span className="text-xs text-slate-400">({kpiId})</span></td>
      <td className={cn('px-4 py-2.5 text-sm text-right font-tabular font-medium', isGood ? 'text-green-700' : 'text-red-700')}>{value}{unit}</td>
      <td className="px-4 py-2.5 text-sm text-right font-tabular text-slate-600">{median}{unit}</td>
      <td className="px-4 py-2.5 text-sm text-right font-tabular text-slate-500">{best}{unit}</td>
    </tr>
  );
}

function ComparisonTable({ children }: { children: React.ReactNode }) {
  return (
    <div className="bg-white rounded-md border border-slate-200 overflow-hidden">
      <div className="px-4 py-3 border-b border-slate-200">
        <h4 className="text-sm font-semibold text-slate-900">Comparaison réseau</h4>
      </div>
      <table className="w-full text-left">
        <thead className="bg-slate-50 border-b border-slate-200">
          <tr>
            <th className="px-4 py-2 text-xs font-semibold text-slate-700">KPI</th>
            <th className="px-4 py-2 text-xs font-semibold text-slate-700 text-right">Institution</th>
            <th className="px-4 py-2 text-xs font-semibold text-slate-700 text-right">Médiane</th>
            <th className="px-4 py-2 text-xs font-semibold text-slate-700 text-right">Meilleur</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-slate-200">
          {children}
        </tbody>
      </table>
    </div>
  );
}

interface TabProps {
  institution: DashboardInstitution;
  ucarMedian: Record<string, number>;
  ucarBest: Record<string, number>;
}

function AcademicTab({ institution, ucarMedian, ucarBest }: TabProps) {
  const series = institutionKpiSeries[institution.code];
  const trendData = series ? series.periods.map((p, i) => ({
    name: p,
    successRate: series.successRate[i],
    curriculumCoverage: series.curriculumCoverage[i],
  })) : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Ratio étudiants/enseignants" value={institution.kpiSnapshot.studentFacultyRatio} icon={Users} badge="ACA-01" />
        <KPICard label="Taux de réussite" value={institution.kpiSnapshot.successRate} suffix="%" icon={TrendingUp} badge="ACA-02" trend={{ value: 1.2, unit: '%' }} />
        <KPICard label="Taux d'abandon" value={institution.kpiSnapshot.dropoutRate} suffix="%" icon={TrendingDown} badge="ACA-03" trend={{ value: -0.2, unit: '%', isPositiveGood: false }} />
        <KPICard label="Couverture programme" value={institution.kpiSnapshot.curriculumCoverage} suffix="%" icon={GraduationCap} badge="ACA-05" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Évolution — réussite et couverture</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" domain={[60, 100]} />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Area type="monotone" dataKey="successRate" stroke="#1d4ed8" strokeWidth={2} fill="#bfdbfe" fillOpacity={0.4} name="Réussite (ACA-02)" />
                <Area type="monotone" dataKey="curriculumCoverage" stroke="#0f766e" strokeWidth={2} fill="#99f6e4" fillOpacity={0.2} name="Couverture (ACA-05)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <ComparisonTable>
          <ComparisonRow label="Ratio étudiants/ens." kpiId="ACA-01" value={institution.kpiSnapshot.studentFacultyRatio} median={ucarMedian['studentFacultyRatio'] ?? 28} best={ucarBest['studentFacultyRatio'] ?? 20.9} unit="" lowerBetter />
          <ComparisonRow label="Taux de réussite" kpiId="ACA-02" value={institution.kpiSnapshot.successRate} median={ucarMedian['successRate']} best={ucarBest['successRate']} />
          <ComparisonRow label="Taux d'abandon" kpiId="ACA-03" value={institution.kpiSnapshot.dropoutRate} median={ucarMedian['dropoutRate']} best={ucarBest['dropoutRate']} lowerBetter />
          <ComparisonRow label="Couverture programme" kpiId="ACA-05" value={institution.kpiSnapshot.curriculumCoverage} median={ucarMedian['curriculumCoverage']} best={ucarBest['curriculumCoverage']} />
        </ComparisonTable>
      </div>
    </div>
  );
}

function SustainabilityTab({ institution, ucarMedian, ucarBest }: TabProps) {
  const esgData = [
    { name: 'Énergie / étudiant', value: institution.kpiSnapshot.energyPerStudent, max: 3000, unit: 'kWh' },
    { name: 'Renouvelable', value: institution.kpiSnapshot.renewableEnergyRate, max: 100, unit: '%' },
    { name: 'Recyclage', value: institution.kpiSnapshot.recyclingRate, max: 100, unit: '%' },
    { name: 'Diversité genre', value: Math.round(institution.kpiSnapshot.genderDiversityIndex * 100), max: 100, unit: '%' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Énergie / étudiant" value={institution.kpiSnapshot.energyPerStudent} suffix=" kWh" icon={Leaf} badge="ESG-01" />
        <KPICard label="Énergie renouvelable" value={institution.kpiSnapshot.renewableEnergyRate} suffix="%" icon={Leaf} badge="ESG-03" />
        <KPICard label="Taux de recyclage" value={institution.kpiSnapshot.recyclingRate} suffix="%" icon={Leaf} badge="ESG-04" />
        <KPICard label="Index diversité genre" value={institution.kpiSnapshot.genderDiversityIndex} icon={Users} badge="ESG-07" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Indicateurs ESG — UI GreenMetric</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={esgData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#E2E8F0" />
                <XAxis type="number" hide />
                <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} width={120} />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Bar dataKey="value" name="Valeur" fill="#0f766e" radius={[0, 4, 4, 0]} barSize={16} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <ComparisonTable>
          <ComparisonRow label="Énergie / étudiant" kpiId="ESG-01" value={institution.kpiSnapshot.energyPerStudent} median={ucarMedian['energyPerStudent'] ?? 1806} best={ucarBest['energyPerStudent'] ?? 1350} unit=" kWh" lowerBetter />
          <ComparisonRow label="Énergie renouvelable" kpiId="ESG-03" value={institution.kpiSnapshot.renewableEnergyRate} median={ucarMedian['renewableEnergyRate']} best={ucarBest['renewableEnergyRate']} />
          <ComparisonRow label="Recyclage" kpiId="ESG-04" value={institution.kpiSnapshot.recyclingRate} median={ucarMedian['recyclingRate']} best={ucarBest['recyclingRate']} />
          <ComparisonRow label="Diversité genre" kpiId="ESG-07" value={institution.kpiSnapshot.genderDiversityIndex} median={ucarMedian['genderDiversityIndex']} best={ucarBest['genderDiversityIndex']} unit="" />
        </ComparisonTable>
      </div>
    </div>
  );
}

function GovernanceTab({ institution, ucarMedian, ucarBest }: TabProps) {
  const series = institutionKpiSeries[institution.code];
  const trendData = series ? series.periods.map((p, i) => ({
    name: p,
    compliance: series.documentControlCompliance[i],
  })) : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Conformité documentaire" value={institution.kpiSnapshot.documentControlCompliance} suffix="%" icon={ShieldCheck} badge="GOV-01" trend={{ value: 1.3, unit: '%' }} />
        <KPICard label="Clôture NCR audit" value={institution.kpiSnapshot.auditNCRClosureRate} suffix="%" icon={ShieldCheck} badge="GOV-02" />
        <KPICard label="Score domaine" value={institution.domainScores.governance} suffix="/100" icon={ShieldCheck} />
        <KPICard label="Alertes gouvernance" value={allAlerts.filter(a => a.institutionCode === institution.code && a.domain === 'Gouvernance' && a.status !== 'resolved').length} icon={AlertCircle} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Évolution — conformité documentaire (GOV-01)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" domain={[60, 100]} />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Area type="monotone" dataKey="compliance" stroke="#1d4ed8" strokeWidth={2} fill="#bfdbfe" fillOpacity={0.4} name="GOV-01" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>

        <ComparisonTable>
          <ComparisonRow label="Conformité doc." kpiId="GOV-01" value={institution.kpiSnapshot.documentControlCompliance} median={ucarMedian['documentControlCompliance']} best={ucarBest['documentControlCompliance']} />
          <ComparisonRow label="Clôture NCR" kpiId="GOV-02" value={institution.kpiSnapshot.auditNCRClosureRate} median={ucarMedian['auditNCRClosureRate']} best={ucarBest['auditNCRClosureRate']} />
        </ComparisonTable>
      </div>
    </div>
  );
}

function HRTab({ institution, ucarMedian, ucarBest }: TabProps) {
  const series = institutionKpiSeries[institution.code];
  const trendData = series ? series.periods.map((p, i) => ({
    name: p,
    workload: series.workloadCompliance[i],
  })) : [];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard label="Conformité charge" value={institution.kpiSnapshot.workloadCompliance} suffix="%" icon={UserRoundCheck} badge="HR-01" trend={{ value: 1.0, unit: '%' }} />
        <KPICard label="Formation accomplie" value={institution.kpiSnapshot.trainingFulfillment} suffix="%" icon={GraduationCap} badge="HR-05" />
        <KPICard label="Score domaine RH" value={institution.domainScores.hr} suffix="/100" icon={Users} />
        <KPICard label="Alertes RH" value={allAlerts.filter(a => a.institutionCode === institution.code && a.domain === 'RH' && a.status !== 'resolved').length} icon={AlertCircle} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-5 rounded-md border border-slate-200">
          <h3 className="text-base font-semibold text-slate-900 mb-4">Évolution — conformité charge (HR-01)</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" domain={[60, 100]} />
                <Tooltip contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }} />
                <Area type="monotone" dataKey="workload" stroke="#b45309" strokeWidth={2} fill="#fde68a" fillOpacity={0.3} name="HR-01" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          {institution.kpiSnapshot.workloadCompliance < 80 && (
            <div className="mt-4 bg-red-50 p-4 rounded-md border border-red-200 flex items-start gap-3">
              <div className="p-2 bg-red-600 rounded text-white">
                <AlertCircle size={16} />
              </div>
              <div>
                <h4 className="text-sm font-semibold text-red-800">Alerte surcharge</h4>
                <p className="text-sm text-red-700 mt-1">
                  La conformité de charge est en dessous du seuil de 80%. Un plan de correction est requis.
                </p>
              </div>
            </div>
          )}
        </div>

        <ComparisonTable>
          <ComparisonRow label="Conformité charge" kpiId="HR-01" value={institution.kpiSnapshot.workloadCompliance} median={ucarMedian['workloadCompliance']} best={ucarBest['workloadCompliance']} />
          <ComparisonRow label="Formation" kpiId="HR-05" value={institution.kpiSnapshot.trainingFulfillment} median={72} best={88.4} />
        </ComparisonTable>
      </div>
    </div>
  );
}

function AccreditationTab({ institution }: { institution: DashboardInstitution }) {
  const frameworks = [
    { key: 'iso9001' as const, name: 'ISO 9001', description: 'Management de la qualité' },
    { key: 'iso21001' as const, name: 'ISO 21001', description: 'Organisations éducatives' },
    { key: 'uiGreenMetric' as const, name: 'UI GreenMetric', description: 'Durabilité universitaire' },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {frameworks.map(fw => {
          const data = institution.accreditation[fw.key];
          const pct = Math.round((data.passingControls / data.totalControls) * 100);
          return (
            <div key={fw.key} className="bg-white p-5 rounded-md border border-slate-200">
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{fw.name}</h3>
                  <p className="text-xs text-slate-500">{fw.description}</p>
                </div>
                <span className={cn(
                  'text-2xl font-bold font-tabular',
                  pct >= 70 ? 'text-green-700' : pct >= 50 ? 'text-amber-600' : 'text-red-700'
                )}>{pct}%</span>
              </div>
              <div className="h-3 bg-slate-100 rounded-full overflow-hidden">
                <div className={cn(
                  'h-full rounded-full transition-all duration-300',
                  pct >= 70 ? 'bg-green-600' : pct >= 50 ? 'bg-amber-500' : 'bg-red-600'
                )} style={{ width: `${pct}%` }} />
              </div>
              <p className="text-xs text-slate-500 mt-2 font-tabular">
                {data.passingControls} / {data.totalControls} contrôles conformes
              </p>
            </div>
          );
        })}
      </div>

      <div className="bg-white p-5 rounded-md border border-slate-200">
        <h3 className="text-base font-semibold text-slate-900 mb-4">Détail par framework</h3>
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-2.5 text-xs font-semibold text-slate-700">Framework</th>
              <th className="px-4 py-2.5 text-xs font-semibold text-slate-700 text-right">Conformes</th>
              <th className="px-4 py-2.5 text-xs font-semibold text-slate-700 text-right">Total</th>
              <th className="px-4 py-2.5 text-xs font-semibold text-slate-700 text-right">Taux</th>
              <th className="px-4 py-2.5 text-xs font-semibold text-slate-700 text-right">Statut</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {frameworks.map(fw => {
              const data = institution.accreditation[fw.key];
              const pct = Math.round((data.passingControls / data.totalControls) * 100);
              return (
                <tr key={fw.key} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm font-medium text-slate-900">{fw.name}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{data.passingControls}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-700">{data.totalControls}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular font-semibold text-slate-900">{pct}%</td>
                  <td className="px-4 py-3 text-right">
                    <span className={cn(
                      'px-2 py-0.5 rounded text-xs font-medium',
                      pct >= 70 ? 'bg-green-50 text-green-700' : pct >= 50 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
                    )}>
                      {pct >= 70 ? 'En bonne voie' : pct >= 50 ? 'À améliorer' : 'Critique'}
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
