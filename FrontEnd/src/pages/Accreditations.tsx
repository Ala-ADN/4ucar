import { useState, useMemo, useEffect, useCallback } from 'react';
import { useToast } from '@/src/components/ui/Toast';
import {
  Search,
  ChevronDown,
  ShieldCheck,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  Clock,
  FileText,
  Cpu,
  UserCheck,
  Sparkles,
  ExternalLink,
  ChevronRight,
  UploadCloud,
  X,
  Loader2,
} from 'lucide-react';
import { cn } from '@/src/lib/utils';
import {
  AccreditationFramework,
  AccreditationStatus,
  AccreditationControl,
  recommendedFrameworks,
} from '@/src/data/accreditationMock';
import {
  ApiError,
  accreditationApi,
  ComplianceLevel,
  ControlStatus,
  FrameworkDetail,
  FrameworkPosture,
  FrameworkSummary,
} from '@/src/lib/api';
import { useAppStore } from '@/src/store';

/* ─── Micro-Components ─── */

function CircularProgress({ percentage, size = 22, strokeWidth = 2.5 }: {
  percentage: number;
  size?: number;
  strokeWidth?: number;
}) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;
  const color =
    percentage >= 80 ? '#16a34a' :
    percentage >= 50 ? '#d97706' :
    '#dc2626';

  return (
    <svg width={size} height={size} className="shrink-0 -rotate-90">
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke="#e2e8f0"
        strokeWidth={strokeWidth}
      />
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        fill="none"
        stroke={color}
        strokeWidth={strokeWidth}
        strokeDasharray={circumference}
        strokeDashoffset={offset}
        strokeLinecap="round"
        className="transition-all duration-500 ease-out"
      />
    </svg>
  );
}

function StatusBadge({ status }: { status: string }) {
  const config: Record<string, { label: string; style: string; icon: typeof CheckCircle2 }> = {
    'En audit': { label: 'En audit', style: 'bg-blue-50 text-blue-700 border border-blue-200/60', icon: Clock },
    'Validé': { label: 'Validé', style: 'bg-emerald-50 text-emerald-700 border border-emerald-200/60', icon: CheckCircle2 },
    'En préparation': { label: 'En préparation', style: 'bg-amber-50 text-amber-700 border border-amber-200/60', icon: AlertTriangle },
    'Expiré': { label: 'Expiré', style: 'bg-red-50 text-red-700 border border-red-200/60', icon: XCircle },
    'Planifié': { label: 'Planifié', style: 'bg-slate-50 text-slate-600 border border-slate-200/60', icon: Clock },
  };

  const c = config[status] || config['Planifié'];
  const Icon = c.icon;

  return (
    <span className={cn('inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-medium', c.style)}>
      <Icon size={13} />
      {c.label}
    </span>
  );
}

function ControlStatusBadge({ status }: { status: AccreditationStatus }) {
  const config: Record<AccreditationStatus, { label: string; style: string; icon: typeof CheckCircle2 }> = {
    PASSING: { label: 'Conforme', style: 'text-emerald-700', icon: CheckCircle2 },
    FAILING: { label: 'Non conforme', style: 'text-red-600', icon: XCircle },
    NEEDS_EVIDENCE: { label: 'Preuve requise', style: 'text-amber-600', icon: AlertTriangle },
    NOT_APPLICABLE: { label: 'N/A', style: 'text-slate-400', icon: MinusCircle },
  };
  const c = config[status];
  const Icon = c.icon;
  return (
    <span className={cn('inline-flex items-center gap-1 text-xs font-medium', c.style)}>
      <Icon size={13} />
      {c.label}
    </span>
  );
}

function DomainChip({ domain }: { domain: string }) {
  return (
    <span className="border border-slate-200 text-xs text-slate-600 px-2 py-0.5 rounded-md font-medium whitespace-nowrap">
      {domain}
    </span>
  );
}

function TestTypeBadge({ type }: { type: string }) {
  const config: Record<string, { label: string; icon: typeof FileText }> = {
    DOCUMENT_UPLOAD: { label: 'Document', icon: FileText },
    AUTOMATED_KPI: { label: 'KPI Auto', icon: Cpu },
    ATTESTATION: { label: 'Attestation', icon: UserCheck },
  };
  const c = config[type] || config.DOCUMENT_UPLOAD;
  const Icon = c.icon;
  return (
    <span className="inline-flex items-center gap-1 text-[10px] text-slate-500 font-medium uppercase tracking-wide">
      <Icon size={11} />
      {c.label}
    </span>
  );
}

/* ─── Main View ─── */

type Tab = 'active' | 'available' | 'history';

const COMPLIANCE_TO_STATUS: Record<ComplianceLevel, AccreditationFramework['status']> = {
  COMPLIANT: 'Validé',
  PARTIAL: 'En audit',
  NON_COMPLIANT: 'En préparation',
};

const CATEGORY_TO_DOMAINS: Record<string, string[]> = {
  QMS: ['Qualité'],
  EOMS: ['Académique'],
  SUSTAINABILITY: ['Environnement'],
};

function mapControl(
  control: ControlStatus,
  detail: FrameworkDetail | undefined,
  category: string,
): AccreditationControl {
  const detailMatch = detail?.controls.find((c) => c.control_id === control.control_id);
  const firstTest = detailMatch?.tests[0];
  const total =
    control.passing_test_ids.length + control.failing_test_ids.length || (detailMatch?.tests.length ?? 0);
  return {
    code: control.clause_ref,
    name: control.name,
    category,
    testType: (firstTest?.test_type as AccreditationControl['testType']) ?? 'DOCUMENT_UPLOAD',
    passingTests: control.passing_test_ids.length,
    totalTests: total,
    ownerRole: 'Resp. Qualité',
    weight: control.weight,
    status: control.status,
    controlId: control.control_id,
    frameworkCode: control.framework_code,
    firstTestId: firstTest?.test_id,
    firstTestTemplateCode: firstTest?.required_template_codes?.[0] ?? undefined,
  };
}

function buildFramework(
  summary: FrameworkSummary,
  detail: FrameworkDetail | undefined,
  posture: FrameworkPosture,
  evidenceCompleted: number,
  evidenceTotal: number,
): AccreditationFramework {
  return {
    id: summary.code,
    code: summary.code,
    name: summary.name,
    version: summary.version,
    scope: 'INSTITUTION',
    domains: CATEGORY_TO_DOMAINS[summary.category] ?? [summary.category || 'Autre'],
    status: COMPLIANCE_TO_STATUS[posture.compliance_level],
    description: summary.description || summary.full_name,
    evidenceCompleted,
    evidenceTotal,
    controlsTotal: posture.total,
    controlsPassing: posture.passing,
    auditDate: `${posture.period_year}-12-31`,
    controls: posture.controls.map((c) => mapControl(c, detail, summary.category)),
  };
}

export function Accreditations() {
  const [activeTab, setActiveTab] = useState<Tab>('active');
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [domainFilter, setDomainFilter] = useState<string>('all');
  const [expandedControl, setExpandedControl] = useState<string | null>(null);
  const { showToast } = useToast();

  const activeInstitutionCode = useAppStore((s) => s.activeInstitutionCode);
  const setActiveInstitutionCode = useAppStore((s) => s.setActiveInstitutionCode);

  const [institutions, setInstitutions] = useState<string[]>([]);
  const [institution, setInstitution] = useState<string>(activeInstitutionCode ?? 'INSAT');
  const [frameworks, setFrameworks] = useState<AccreditationFramework[]>([]);
  const [uploadModalControl, setUploadModalControl] = useState<AccreditationControl | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load list of demo institutions once.
  useEffect(() => {
    accreditationApi
      .listInstitutions()
      .then((list) => {
        setInstitutions(list);
        if (!list.includes(institution) && list.length > 0) {
          setInstitution(list[0]);
        }
      })
      .catch((err: unknown) => {
        const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
        setError(`Failed to load institutions: ${msg}`);
      });
    // run once on mount
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Load active frameworks for the selected institution.
  const loadFrameworks = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const summaries = await accreditationApi.listFrameworks();
      const enriched = await Promise.all(
        summaries.map(async (summary) => {
          const [detail, posture, evidence] = await Promise.all([
            accreditationApi.getFramework(summary.code),
            accreditationApi.status(summary.code, institution),
            accreditationApi.evidence(summary.code, institution),
          ]);
          return buildFramework(summary, detail, posture, evidence.approved, evidence.total_evidence);
        }),
      );
      setFrameworks(enriched);
    } catch (err) {
      const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
      setError(msg);
      setFrameworks([]);
    } finally {
      setLoading(false);
    }
  }, [institution]);

  useEffect(() => {
    void loadFrameworks();
  }, [loadFrameworks]);

  useEffect(() => {
    setActiveInstitutionCode(institution);
  }, [institution, setActiveInstitutionCode]);

  const filteredFrameworks = useMemo(() => {
    return frameworks.filter((fw) => {
      const matchSearch =
        fw.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        fw.code.toLowerCase().includes(searchTerm.toLowerCase());
      const matchStatus = statusFilter === 'all' || fw.status === statusFilter;
      const matchDomain = domainFilter === 'all' || fw.domains.includes(domainFilter);
      return matchSearch && matchStatus && matchDomain;
    });
  }, [frameworks, searchTerm, statusFilter, domainFilter]);

  const allDomains = useMemo(() => {
    const set = new Set<string>();
    frameworks.forEach((fw) => fw.domains.forEach((d) => set.add(d)));
    return Array.from(set);
  }, [frameworks]);

  const allStatuses = useMemo(() => {
    const set = new Set<string>();
    frameworks.forEach((fw) => set.add(fw.status));
    return Array.from(set);
  }, [frameworks]);

  // Approve evidence via the live backend, then refetch the affected framework.
  const handleSimulateUpload = async () => {
    if (!uploadModalControl) return;
    const ctrl = uploadModalControl;
    const fwCode = ctrl.frameworkCode;
    const controlId = ctrl.controlId;
    const testId = ctrl.firstTestId;
    setUploadModalControl(null);

    if (!fwCode || !controlId || !testId) {
      showToast('Action indisponible (contrôle non synchronisé).', 'warning');
      return;
    }

    try {
      const result = await accreditationApi.approveEvidence(fwCode, controlId, institution, {
        test_id: testId,
        doc_name: 'Preuve soumise via démo',
        template_code: ctrl.firstTestTemplateCode ?? null,
      });
      showToast(
        `Preuve validée — ${ctrl.code} : ${ctrl.name} → ${result.updated_control_status.status}`,
        'success',
      );
      await loadFrameworks();
    } catch (err) {
      const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
      showToast(`Échec — ${msg}`, 'error');
    }
  };

  return (
    <div className="space-y-6">
      {/* ── Header ── */}
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <ShieldCheck size={22} className="text-blue-800" />
            <h1 className="text-xl font-semibold text-slate-900">Accréditations & Conformité</h1>
            {loading && <Loader2 size={16} className="animate-spin text-blue-700" />}
          </div>
          <p className="text-sm text-slate-500 pl-[34px]">
            Suivi de conformité des référentiels actifs, en préparation et historiques.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <label htmlFor="acc-institution" className="text-xs text-slate-500 uppercase tracking-wide">
            Institution
          </label>
          <select
            id="acc-institution"
            value={institution}
            onChange={(e) => setInstitution(e.target.value)}
            className="bg-white border border-slate-200 rounded-md px-3 py-1.5 text-sm text-slate-700 outline-none focus:border-blue-700"
          >
            {institutions.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
            {!institutions.includes(institution) && (
              <option value={institution}>{institution}</option>
            )}
          </select>
        </div>
      </div>
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-2">
          Impossible de charger les référentiels — {error}
        </div>
      )}

      {/* ── Tabs ── */}
      <div className="border-b border-slate-200">
        <nav className="flex gap-8 -mb-px">
          {([
            { key: 'active' as Tab, label: 'Actives', count: frameworks.length },
            { key: 'available' as Tab, label: 'Disponibles', count: recommendedFrameworks.length },
            { key: 'history' as Tab, label: 'Historique', count: 0 },
          ]).map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={cn(
                'pb-3 text-sm font-medium transition-colors duration-150 border-b-2',
                activeTab === tab.key
                  ? 'text-slate-900 border-blue-800'
                  : 'text-slate-500 hover:text-slate-700 border-transparent'
              )}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={cn(
                  'ml-2 text-xs px-1.5 py-0.5 rounded-full font-tabular',
                  activeTab === tab.key ? 'bg-blue-100 text-blue-800' : 'bg-slate-100 text-slate-500'
                )}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </nav>
      </div>

      {/* ── Tab: Actives ── */}
      {activeTab === 'active' && (
        <>
          {/* Filter Toolbar */}
          <div className="flex flex-wrap items-center gap-3">
            <div className="relative flex-1 min-w-60 max-w-sm">
              <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                placeholder="Rechercher un référentiel..."
                className="w-full bg-white border border-slate-200 rounded-md pl-9 pr-4 py-2 text-sm outline-none focus:border-blue-700 placeholder:text-slate-400"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <DropdownFilter
              label="Statut"
              value={statusFilter}
              onChange={setStatusFilter}
              options={[{ value: 'all', label: 'Tous' }, ...allStatuses.map((s) => ({ value: s, label: s }))]}
            />
            <DropdownFilter
              label="Domaine"
              value={domainFilter}
              onChange={setDomainFilter}
              options={[{ value: 'all', label: 'Tous' }, ...allDomains.map((d) => ({ value: d, label: d }))]}
            />
          </div>

          {/* Main Table */}
          <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-slate-200/80">
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Référentiel</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-center">Preuves</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-center">Contrôles</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Échéance d'audit</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Statut</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">Domaine</th>
                  <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider"></th>
                </tr>
              </thead>
              <tbody>
                {filteredFrameworks.map((fw) => {
                  const evidPct = Math.round((fw.evidenceCompleted / fw.evidenceTotal) * 100);
                  const ctrlPct = Math.round((fw.controlsPassing / fw.controlsTotal) * 100);
                  const isExpanded = expandedControl === fw.id;

                  return (
                    <FrameworkRow
                      key={fw.id}
                      fw={fw}
                      evidPct={evidPct}
                      ctrlPct={ctrlPct}
                      isExpanded={isExpanded}
                      onToggle={() => setExpandedControl(isExpanded ? null : fw.id)}
                      onRequestUpload={setUploadModalControl}
                    />
                  );
                })}
              </tbody>
            </table>

            {filteredFrameworks.length === 0 && (
              <div className="py-16 text-center text-sm text-slate-500">
                Aucun référentiel ne correspond aux filtres sélectionnés.
              </div>
            )}
          </div>

          {/* Recommandations */}
          <RecommendationsSection />
        </>
      )}

      {/* ── Tab: Disponibles ── */}
      {activeTab === 'available' && <AvailableTab />}

      {/* ── Tab: Historique ── */}
      {activeTab === 'history' && (
        <div className="py-16 text-center text-sm text-slate-500">
          <Clock size={32} className="mx-auto mb-3 text-slate-300" />
          Aucune accréditation archivée pour le moment.
        </div>
      )}

      {/* ── Upload Modal ── */}
      {uploadModalControl && (
        <UploadModal 
          control={uploadModalControl} 
          onClose={() => setUploadModalControl(null)} 
          onValidate={handleSimulateUpload} 
        />
      )}
    </div>
  );
}

/* ─── Framework Row with expandable controls ─── */

function FrameworkRow({
  fw,
  evidPct,
  ctrlPct,
  isExpanded,
  onToggle,
  onRequestUpload,
}: {
  fw: AccreditationFramework;
  evidPct: number;
  ctrlPct: number;
  isExpanded: boolean;
  onToggle: () => void;
  onRequestUpload: (ctrl: AccreditationControl) => void;
}) {
  const fwIcon: Record<string, string> = {
    ISO9001: '🏛️',
    ISO21001: '🎓',
    GREENMETRIC: '🌿',
  };

  const sortedControls = [...fw.controls].sort((a, b) => {
    const priority: Record<AccreditationStatus, number> = { FAILING: 0, NEEDS_EVIDENCE: 1, PASSING: 2, NOT_APPLICABLE: 3 };
    const p = (priority[a.status] ?? 4) - (priority[b.status] ?? 4);
    return p !== 0 ? p : b.weight - a.weight;
  });

  return (
    <>
      <tr
        onClick={onToggle}
        className={cn(
          'border-b border-slate-200/50 cursor-pointer transition-colors duration-100',
          isExpanded ? 'bg-slate-50/80' : 'hover:bg-slate-50/50'
        )}
      >
        {/* Référentiel */}
        <td className="py-4 px-6">
          <div className="flex items-center gap-3">
            <span className="text-lg leading-none">{fwIcon[fw.code] || '📋'}</span>
            <div>
              <p className="text-sm font-medium text-slate-900">{fw.name}</p>
              <p className="text-xs text-slate-500 mt-0.5">{fw.scope === 'NETWORK' ? 'Réseau' : 'Institution'} · v{fw.version}</p>
            </div>
          </div>
        </td>
        {/* Preuves */}
        <td className="py-4 px-6">
          <div className="flex items-center justify-center gap-2">
            <CircularProgress percentage={evidPct} />
            <span className="text-sm font-medium text-slate-900 tabular-nums">{evidPct}%</span>
          </div>
        </td>
        {/* Contrôles */}
        <td className="py-4 px-6">
          <div className="flex items-center justify-center gap-2">
            <CircularProgress percentage={ctrlPct} />
            <span className="text-sm font-medium text-slate-900 tabular-nums">
              {fw.controlsPassing}/{fw.controlsTotal}
            </span>
          </div>
        </td>
        {/* Échéance */}
        <td className="py-4 px-6">
          <span className="text-sm text-slate-700 tabular-nums">
            {new Date(fw.auditDate).toLocaleDateString('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' })}
          </span>
        </td>
        {/* Statut */}
        <td className="py-4 px-6">
          <StatusBadge status={fw.status} />
        </td>
        {/* Domaine */}
        <td className="py-4 px-6">
          <div className="flex flex-wrap gap-1.5">
            {fw.domains.map((d) => <DomainChip key={d} domain={d} />)}
          </div>
        </td>
        {/* Arrow */}
        <td className="py-4 px-6">
          <ChevronRight
            size={16}
            className={cn(
              'text-slate-400 transition-transform duration-200',
              isExpanded && 'rotate-90'
            )}
          />
        </td>
      </tr>

      {/* ── Expanded Controls Panel ── */}
      {isExpanded && (
        <tr>
          <td colSpan={7} className="p-0">
            <div className="bg-slate-50/60 border-b border-slate-200/50">
              {/* Framework description */}
              <div className="px-8 py-4 border-b border-slate-200/40">
                <p className="text-sm text-slate-600 max-w-3xl leading-relaxed">{fw.description}</p>
              </div>

              {/* Controls sub-table */}
              <div className="px-6">
                <table className="w-full text-left">
                  <thead>
                    <tr>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider w-32">Code</th>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider">Contrôle</th>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider">Type</th>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider text-center">Tests</th>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider">Resp.</th>
                      <th className="py-2.5 px-3 text-[11px] font-medium text-slate-400 uppercase tracking-wider text-right">Statut</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedControls.map((ctrl) => (
                      <tr 
                        key={ctrl.code} 
                        className={cn(
                          "border-b border-slate-200/30 transition-all duration-150",
                          ctrl.status === 'NEEDS_EVIDENCE' 
                            ? 'cursor-pointer hover:bg-slate-100 hover:ring-1 hover:ring-inset hover:ring-[#1d5394] relative z-10' 
                            : 'hover:bg-white/60'
                        )}
                        onClick={() => ctrl.status === 'NEEDS_EVIDENCE' && onRequestUpload(ctrl)}
                      >
                        <td className="py-3 px-3 text-xs font-mono text-slate-500 tabular-nums">{ctrl.code}</td>
                        <td className="py-3 px-3">
                          <div>
                            <p className="text-sm text-slate-800 font-medium">{ctrl.name}</p>
                            <p className="text-xs text-slate-400 mt-0.5">{ctrl.category}</p>
                          </div>
                        </td>
                        <td className="py-3 px-3">
                          <TestTypeBadge type={ctrl.testType} />
                        </td>
                        <td className="py-3 px-3 text-center">
                          <span className={cn(
                            "text-xs font-medium tabular-nums px-1.5 py-0.5 rounded",
                            ctrl.status === 'NEEDS_EVIDENCE' ? "bg-amber-100 text-amber-700" : "text-slate-600"
                          )}>
                            {ctrl.passingTests}/{ctrl.totalTests}
                          </span>
                        </td>
                        <td className="py-3 px-3 text-xs text-slate-500">{ctrl.ownerRole}</td>
                        <td className="py-3 px-3 text-right">
                          <ControlStatusBadge status={ctrl.status} />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

/* ─── Dropdown Filter ─── */

function DropdownFilter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="appearance-none bg-white border border-slate-200 rounded-md pl-3 pr-8 py-2 text-sm text-slate-700 outline-none focus:border-blue-700 cursor-pointer"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {label}: {opt.label}
          </option>
        ))}
      </select>
      <ChevronDown size={14} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none" />
    </div>
  );
}

/* ─── Recommendations Section ─── */

function RecommendationsSection() {
  return (
    <div className="mt-2">
      <div className="flex items-center gap-2 mb-4">
        <Sparkles size={16} className="text-amber-500" />
        <h3 className="text-sm font-semibold text-slate-900">Recommandations — référentiels cibles</h3>
      </div>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {recommendedFrameworks.map((fw) => (
          <div
            key={fw.code}
            className="group bg-white border border-slate-200 rounded-lg p-4 hover:border-blue-300 hover:shadow-sm transition-all duration-200 cursor-pointer"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm font-semibold text-slate-900">{fw.code}</p>
                <p className="text-xs text-slate-500 mt-0.5">{fw.name}</p>
              </div>
              <ExternalLink size={14} className="text-slate-300 group-hover:text-blue-600 transition-colors duration-150 mt-0.5" />
            </div>
            <p className="text-xs text-slate-600 leading-relaxed mb-3 line-clamp-3">{fw.description}</p>
            <div className="flex items-center justify-between">
              <div className="flex gap-1.5">
                {fw.domains.map((d) => <DomainChip key={d} domain={d} />)}
              </div>
              <span className={cn(
                'text-[10px] font-medium uppercase tracking-wide px-1.5 py-0.5 rounded',
                fw.difficulty === 'Faible' ? 'bg-green-50 text-green-700' :
                fw.difficulty === 'Moyen' ? 'bg-amber-50 text-amber-700' :
                'bg-red-50 text-red-700'
              )}>
                {fw.difficulty}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Available Tab ─── */

function AvailableTab() {
  return (
    <div className="space-y-6">
      <p className="text-sm text-slate-600">
        Référentiels additionnels que l'Université de Carthage pourrait viser pour renforcer sa reconnaissance internationale.
      </p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {recommendedFrameworks.map((fw) => (
          <div
            key={fw.code}
            className="bg-white border border-slate-200 rounded-lg p-5 hover:border-blue-300 transition-all duration-200"
          >
            <div className="flex items-start justify-between mb-3">
              <div>
                <h3 className="text-base font-semibold text-slate-900">{fw.name}</h3>
                <p className="text-xs text-slate-500 mt-0.5">{fw.code}</p>
              </div>
              <span className={cn(
                'text-xs font-medium px-2.5 py-1 rounded-md',
                fw.difficulty === 'Faible' ? 'bg-green-50 text-green-700 border border-green-200/60' :
                fw.difficulty === 'Moyen' ? 'bg-amber-50 text-amber-700 border border-amber-200/60' :
                'bg-red-50 text-red-700 border border-red-200/60'
              )}>
                Difficulté: {fw.difficulty}
              </span>
            </div>
            <p className="text-sm text-slate-600 leading-relaxed mb-4">{fw.description}</p>
            <div className="flex items-center justify-between">
              <div className="flex gap-2">
                {fw.domains.map((d) => <DomainChip key={d} domain={d} />)}
              </div>
              <button className="px-3 py-1.5 text-sm font-medium text-blue-800 hover:bg-blue-50 rounded-md transition-colors duration-150">
                Explorer →
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ─── Upload Modal (PoC) ─── */

function UploadModal({
  control,
  onClose,
  onValidate,
}: {
  control: AccreditationControl;
  onClose: () => void;
  onValidate: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 opacity-0 animate-[fadeIn_0.2s_ease-out_forwards]">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-slate-900/40 backdrop-blur-sm"
        onClick={onClose}
      />
      
      {/* Modal panel */}
      <div className="relative bg-white rounded-xl shadow-2xl w-full max-w-lg overflow-hidden translate-y-4 animate-[slideUp_0.3s_ease-out_forwards]">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200">
          <h2 className="text-lg font-semibold text-[#0F172A] tracking-tight">Soumettre une preuve documentaire</h2>
          <button 
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors duration-150"
          >
            <X size={18} />
          </button>
        </div>
        
        <div className="p-6 space-y-5">
          {/* Context */}
          <div className="bg-[#F0F5FA] border border-[#E8EFF6] rounded-lg p-4">
            <span className="text-[10px] font-bold text-[#1d5394] uppercase tracking-wider bg-white px-1.5 py-0.5 rounded shadow-sm">
              {control.code}
            </span>
            <p className="text-sm font-medium text-[#0F172A] mt-2 leading-snug">{control.name}</p>
            <p className="text-xs text-[#4A7DC0] mt-1">{control.category}</p>
          </div>
          
          {/* Dropzone */}
          <div className="border-2 border-dashed border-slate-300 bg-slate-50 hover:bg-slate-100 hover:border-blue-400 transition-colors duration-200 rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer group">
            <div className="w-12 h-12 rounded-full bg-white shadow-sm flex items-center justify-center mb-4 group-hover:scale-110 group-hover:shadow transition-all duration-200">
              <UploadCloud size={24} className="text-slate-400 group-hover:text-blue-500" />
            </div>
            <p className="text-sm font-medium text-slate-700">
              Glissez votre document PDF ici ou <span className="text-[#1d5394] hover:underline">parcourez</span>
            </p>
            <p className="text-xs text-slate-400 mt-1.5">PDF sécurisé, max 10 Mo. Vérification IA incluse.</p>
          </div>
        </div>
        
        <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 flex justify-end gap-3">
          <button 
            onClick={onClose}
            className="px-4 py-2 text-sm font-medium text-slate-600 hover:text-slate-800 transition-colors duration-150"
          >
            Annuler
          </button>
          <button 
            onClick={onValidate}
            className="px-6 py-2 bg-[#1d5394] text-white text-sm font-semibold rounded-lg hover:bg-[#153d6e] shadow-sm active:scale-95 transition-all duration-150"
          >
            Valider le document
          </button>
        </div>
      </div>
{/* ── Keyframes inline for simplicity ── */}
<style>{`
  @keyframes fadeIn {
    to { opacity: 1; }
  }
  @keyframes slideUp {
    to { transform: translateY(0); }
  }
`}</style>
    </div>
  );
}
