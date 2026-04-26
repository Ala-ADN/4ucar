import { useState, useEffect, useMemo, useCallback } from 'react';
import {
  GraduationCap,
  Search,
  Loader2,
  ChevronDown,
  ChevronRight,
  X,
  Award,
  Building2,
  Mail,
  ExternalLink,
  Sparkles,
  ArrowUpDown,
  TrendingUp,
  CheckCircle2,
  BookOpen,
} from 'lucide-react';
import { cn } from '@/src/lib/utils';
import {
  ApiError,
  professorsApi,
  ProfessorListItem,
  ProfessorDetail,
  ProfessorFilters,
  ProfessorSort,
  MatchCandidate,
} from '@/src/lib/api';
import { useToast } from '@/src/components/ui/Toast';

/* ─── Helpers ──────────────────────────────────────────────────────────── */

function fullName(p: { first_name: string; last_name: string }): string {
  return `${p.first_name} ${p.last_name}`;
}

function initials(p: { first_name: string; last_name: string }): string {
  return (p.first_name[0] ?? '') + (p.last_name[0] ?? '');
}

function formatNumber(n: number): string {
  return n.toLocaleString('fr-FR');
}

const RANK_BADGE_STYLES: Record<string, string> = {
  Professeur: 'bg-blue-50 text-blue-800 border-blue-200/60',
  'Maître de Conférences': 'bg-violet-50 text-violet-700 border-violet-200/60',
  'Maître Assistant': 'bg-slate-50 text-slate-700 border-slate-200/60',
  PES: 'bg-amber-50 text-amber-700 border-amber-200/60',
};

/* ─── Page ─────────────────────────────────────────────────────────────── */

export function Professors() {
  const { showToast } = useToast();
  const [filters, setFilters] = useState<ProfessorFilters | null>(null);
  const [items, setItems] = useState<ProfessorListItem[]>([]);
  const [total, setTotal] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [department, setDepartment] = useState<string>('');
  const [rank, setRank] = useState<string>('');
  const [sort, setSort] = useState<ProfessorSort>('h_index_desc');

  const [activeId, setActiveId] = useState<string | null>(null);
  const [detail, setDetail] = useState<ProfessorDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);

  // Debounce the search input → committed `search` for the request.
  useEffect(() => {
    const t = setTimeout(() => setSearch(searchInput.trim()), 300);
    return () => clearTimeout(t);
  }, [searchInput]);

  // Load filter facets once.
  useEffect(() => {
    professorsApi
      .filters()
      .then(setFilters)
      .catch((err: unknown) => {
        const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
        setError(`Filtres: ${msg}`);
      });
  }, []);

  // Load list whenever a filter changes.
  const loadList = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await professorsApi.list({
        search: search || undefined,
        department: department || undefined,
        rank: rank || undefined,
        sort,
        limit: 200,
      });
      setItems(res.items);
      setTotal(res.total);
    } catch (err) {
      const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
      setError(msg);
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [search, department, rank, sort]);

  useEffect(() => {
    void loadList();
  }, [loadList]);

  // Pull detail when a row is selected.
  useEffect(() => {
    if (!activeId) {
      setDetail(null);
      return;
    }
    let cancelled = false;
    setDetailLoading(true);
    professorsApi
      .detail(activeId)
      .then((d) => {
        if (!cancelled) setDetail(d);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
        showToast(`Détails indisponibles — ${msg}`, 'error');
        setActiveId(null);
      })
      .finally(() => {
        if (!cancelled) setDetailLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeId, showToast]);

  const stats = useMemo(() => {
    const withH = items.filter((p) => p.h_index !== null);
    const topH = withH.reduce((m, p) => Math.max(m, p.h_index ?? 0), 0);
    const totalCitations = items.reduce((s, p) => s + (p.total_citations ?? 0), 0);
    return {
      totalShown: items.length,
      withHIndex: withH.length,
      topH,
      totalCitations,
    };
  }, [items]);

  const onToggleSort = () =>
    setSort((s) => (s === 'h_index_desc' ? 'name_asc' : 'h_index_desc'));

  return (
    <div className="space-y-6">
      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <GraduationCap size={22} className="text-blue-800" />
            <h1 className="text-xl font-semibold text-slate-900">
              Corps Enseignant
            </h1>
            {loading && <Loader2 size={16} className="animate-spin text-blue-700" />}
          </div>
          <p className="text-sm text-slate-500 pl-[34px]">
            Annuaire des enseignants-chercheurs avec h-index, publications et moteur de
            correspondance par spécialité.
          </p>
        </div>
        <div className="text-xs text-slate-500 tabular-nums">
          {total} enseignant{total > 1 ? 's' : ''} au total
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-2">
          {error}
        </div>
      )}

      {/* ── Stats strip ─────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <StatTile
          label="Visibles"
          value={formatNumber(stats.totalShown)}
          hint={`sur ${total}`}
          icon={GraduationCap}
        />
        <StatTile
          label="Avec h-index"
          value={`${stats.withHIndex}/${stats.totalShown}`}
          hint="OpenAlex"
          icon={Award}
        />
        <StatTile
          label="h-index max"
          value={String(stats.topH)}
          hint="dans la sélection"
          icon={TrendingUp}
        />
        <StatTile
          label="Citations cumulées"
          value={formatNumber(stats.totalCitations)}
          hint="sélection visible"
          icon={BookOpen}
        />
      </div>

      {/* ── Match widget ────────────────────────────────────────────────── */}
      <MatchPanel filters={filters} />

      {/* ── Filter toolbar ──────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-60 max-w-sm">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher par nom, email ou spécialité…"
            className="w-full bg-white border border-slate-200 rounded-md pl-9 pr-4 py-2 text-sm outline-none focus:border-blue-700 placeholder:text-slate-400"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
        </div>

        <FilterSelect
          label="Département"
          value={department}
          onChange={setDepartment}
          options={[
            { value: '', label: 'Tous' },
            ...(filters?.departments ?? []).map((d) => ({
              value: d.code,
              label: `${d.code} (${d.count})`,
            })),
          ]}
        />
        <FilterSelect
          label="Grade"
          value={rank}
          onChange={setRank}
          options={[
            { value: '', label: 'Tous' },
            ...(filters?.ranks ?? []).map((r) => ({
              value: r.value,
              label: `${r.value} (${r.count})`,
            })),
          ]}
        />

        <div className="ml-auto">
          <button
            onClick={onToggleSort}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-md border border-slate-200 bg-white hover:border-slate-300 transition-colors duration-150"
            title="Inverser le tri"
          >
            <ArrowUpDown size={13} />
            {sort === 'h_index_desc' ? 'Tri : h-index ↓' : 'Tri : nom A→Z'}
          </button>
        </div>
      </div>

      {/* ── Table ───────────────────────────────────────────────────────── */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-slate-200/80">
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Enseignant
              </th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Département
              </th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Grade
              </th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider">
                Spécialité
              </th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-center">
                h-index
              </th>
              <th className="py-3 px-6 text-xs font-medium text-slate-500 uppercase tracking-wider text-right">
                Publications
              </th>
              <th className="py-3 px-6"></th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <ProfessorRow
                key={p.id}
                p={p}
                isActive={activeId === p.id}
                onSelect={() => setActiveId(p.id)}
              />
            ))}
          </tbody>
        </table>
        {!loading && items.length === 0 && (
          <div className="py-16 text-center text-sm text-slate-500">
            Aucun enseignant ne correspond aux filtres.
          </div>
        )}
      </div>

      {/* ── Detail drawer ───────────────────────────────────────────────── */}
      {activeId && (
        <DetailDrawer
          loading={detailLoading}
          detail={detail}
          onClose={() => setActiveId(null)}
        />
      )}
    </div>
  );
}

/* ─── Stat tile ────────────────────────────────────────────────────────── */

function StatTile({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint?: string;
  icon: typeof GraduationCap;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-tight">{label}</p>
        <Icon size={14} className="text-slate-400" />
      </div>
      <p className="text-2xl font-semibold text-slate-900 mt-1 tabular-nums">{value}</p>
      {hint && <p className="text-xs text-slate-400 mt-0.5">{hint}</p>}
    </div>
  );
}

/* ─── Filter dropdown ──────────────────────────────────────────────────── */

function FilterSelect({
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
      <ChevronDown
        size={14}
        className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none"
      />
    </div>
  );
}

/* ─── One row ──────────────────────────────────────────────────────────── */

function ProfessorRow({
  p,
  isActive,
  onSelect,
}: {
  p: ProfessorListItem;
  isActive: boolean;
  onSelect: () => void;
}) {
  const rankStyle = p.rank ? RANK_BADGE_STYLES[p.rank] ?? 'bg-slate-50 text-slate-700 border-slate-200/60' : '';

  return (
    <tr
      onClick={onSelect}
      className={cn(
        'border-b border-slate-200/50 cursor-pointer transition-colors duration-100',
        isActive ? 'bg-slate-50/80' : 'hover:bg-slate-50/50',
      )}
    >
      <td className="py-3.5 px-6">
        <div className="flex items-center gap-3">
          <Avatar p={p} />
          <div className="min-w-0">
            <p className="text-sm font-medium text-slate-900 truncate">
              {fullName(p)}
            </p>
            <p className="text-xs text-slate-500 truncate">{p.email}</p>
          </div>
        </div>
      </td>
      <td className="py-3.5 px-6">
        <span className="text-xs font-semibold text-slate-600 bg-slate-50 border border-slate-200/80 px-2 py-0.5 rounded-md">
          {p.department_code ?? '—'}
        </span>
      </td>
      <td className="py-3.5 px-6">
        {p.rank ? (
          <span className={cn('inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium border', rankStyle)}>
            {p.rank}
          </span>
        ) : (
          <span className="text-xs text-slate-400">—</span>
        )}
      </td>
      <td className="py-3.5 px-6">
        <p className="text-sm text-slate-600 truncate max-w-xs">
          {p.primary_specialty ?? '—'}
        </p>
      </td>
      <td className="py-3.5 px-6 text-center">
        <HIndexCell value={p.h_index} />
      </td>
      <td className="py-3.5 px-6 text-right">
        <div className="text-sm text-slate-700 tabular-nums">
          {formatNumber(p.publications_count)}
        </div>
        <div className="text-[10px] text-slate-400 tabular-nums">
          {formatNumber(p.total_citations)} cit.
        </div>
      </td>
      <td className="py-3.5 px-6 w-8">
        <ChevronRight
          size={16}
          className={cn(
            'text-slate-400 transition-transform duration-200',
            isActive && 'rotate-90',
          )}
        />
      </td>
    </tr>
  );
}

function Avatar({ p }: { p: { first_name: string; last_name: string } }) {
  return (
    <div className="h-9 w-9 rounded-full bg-gradient-to-br from-blue-100 to-blue-50 border border-blue-100 text-blue-800 flex items-center justify-center text-xs font-semibold shrink-0">
      {initials(p)}
    </div>
  );
}

function HIndexCell({ value }: { value: number | null }) {
  if (value === null) {
    return (
      <span className="inline-flex items-center text-[11px] text-slate-400 italic">
        non indexé
      </span>
    );
  }
  // 0 / 1-5 / 6-15 / 16+ tiers
  const tier =
    value >= 16 ? 'top' : value >= 6 ? 'mid' : value >= 1 ? 'low' : 'zero';
  const styles: Record<string, string> = {
    top: 'bg-emerald-50 text-emerald-700 border-emerald-200/60',
    mid: 'bg-blue-50 text-blue-700 border-blue-200/60',
    low: 'bg-slate-50 text-slate-700 border-slate-200/60',
    zero: 'bg-amber-50 text-amber-700 border-amber-200/60',
  };
  return (
    <span
      className={cn(
        'inline-flex items-center justify-center min-w-[2.25rem] px-2 py-0.5 rounded-md text-sm font-semibold border tabular-nums',
        styles[tier],
      )}
    >
      {value}
    </span>
  );
}

/* ─── Detail drawer ────────────────────────────────────────────────────── */

function DetailDrawer({
  loading,
  detail,
  onClose,
}: {
  loading: boolean;
  detail: ProfessorDetail | null;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 flex animate-[fadeIn_0.2s_ease-out_forwards] opacity-0">
      <div
        className="absolute inset-0 bg-slate-900/30 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div className="relative ml-auto w-full max-w-xl h-full bg-white shadow-2xl border-l border-slate-200 overflow-y-auto translate-x-4 animate-[slideLeft_0.25s_ease-out_forwards]">
        {/* Header */}
        <div className="sticky top-0 bg-white border-b border-slate-200 px-6 py-4 flex items-start justify-between gap-3 z-10">
          {detail ? (
            <div className="flex items-start gap-3 min-w-0">
              <Avatar p={detail} />
              <div className="min-w-0">
                <h2 className="text-lg font-semibold text-slate-900 leading-tight">
                  {fullName(detail)}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5 flex items-center gap-2">
                  <Mail size={11} />
                  {detail.email}
                </p>
              </div>
            </div>
          ) : (
            <p className="text-sm text-slate-500">Chargement…</p>
          )}
          <button
            onClick={onClose}
            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-md transition-colors duration-150 shrink-0"
            aria-label="Fermer"
          >
            <X size={18} />
          </button>
        </div>

        {loading || !detail ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 size={24} className="animate-spin text-slate-400" />
          </div>
        ) : (
          <div className="p-6 space-y-6">
            {/* Identity card */}
            <div className="grid grid-cols-2 gap-3">
              <InfoCell label="Département" value={detail.department_code ?? '—'} icon={Building2} />
              <InfoCell label="Grade" value={detail.rank ?? '—'} icon={Award} />
              <InfoCell label="Spécialité" value={detail.primary_specialty ?? '—'} colSpan={2} />
            </div>

            {/* Research stats */}
            <div className="bg-gradient-to-br from-[#1d5394] to-[#153d6e] text-white rounded-xl p-5">
              <p className="text-xs uppercase tracking-wider opacity-70 mb-3">
                Profil de recherche · OpenAlex
              </p>
              <div className="grid grid-cols-3 gap-4">
                <ResearchStat label="h-index" value={detail.h_index ?? '—'} />
                <ResearchStat label="Publications" value={formatNumber(detail.publications_count)} />
                <ResearchStat label="Citations" value={formatNumber(detail.total_citations)} />
              </div>
              {detail.h_index_updated_at && (
                <p className="text-[10px] opacity-60 mt-3">
                  Synchronisé le{' '}
                  {new Date(detail.h_index_updated_at).toLocaleDateString('fr-FR', {
                    day: '2-digit',
                    month: 'short',
                    year: 'numeric',
                  })}
                </p>
              )}
            </div>

            {/* Specializations */}
            {detail.specializations.length > 0 && (
              <Section title="Spécialisations" count={detail.specializations.length}>
                <div className="flex flex-wrap gap-2">
                  {detail.specializations.map((s, i) => (
                    <span
                      key={i}
                      className={cn(
                        'inline-flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-md border',
                        s.verified
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200/60'
                          : 'bg-slate-50 text-slate-700 border-slate-200/60',
                      )}
                    >
                      {s.verified && <CheckCircle2 size={11} />}
                      {s.domain}
                      {s.subdomain && <span className="opacity-60">· {s.subdomain}</span>}
                    </span>
                  ))}
                </div>
              </Section>
            )}

            {/* Top publications */}
            {detail.top_publications.length > 0 && (
              <Section title="Publications les plus citées" count={detail.top_publications.length}>
                <ul className="space-y-2">
                  {detail.top_publications.map((pub, i) => (
                    <li key={i} className="border border-slate-200 rounded-md p-3 bg-white">
                      <p className="text-sm text-slate-800 font-medium leading-snug">
                        {pub.title}
                      </p>
                      <div className="flex items-center gap-3 mt-1.5 text-xs text-slate-500">
                        {pub.year && <span className="tabular-nums">{pub.year}</span>}
                        <span className="tabular-nums">
                          {formatNumber(pub.citation_count)} cit.
                        </span>
                        {pub.doi && (
                          <a
                            href={`https://doi.org/${pub.doi}`}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-blue-700 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            DOI <ExternalLink size={10} />
                          </a>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {detail.top_publications.length === 0 && (
              <div className="text-center text-sm text-slate-500 italic py-6 border border-dashed border-slate-200 rounded-md">
                Aucune publication indexée. L'enrichissement OpenAlex peut être relancé
                par le script <code className="text-xs">scripts/enrich_professors_openalex.py</code>.
              </div>
            )}
          </div>
        )}

        <style>{`
          @keyframes fadeIn { to { opacity: 1; } }
          @keyframes slideLeft { to { transform: translateX(0); } }
        `}</style>
      </div>
    </div>
  );
}

function InfoCell({
  label,
  value,
  icon: Icon,
  colSpan,
}: {
  label: string;
  value: string;
  icon?: typeof Building2;
  colSpan?: number;
}) {
  return (
    <div
      className={cn(
        'border border-slate-200 rounded-md p-3 bg-slate-50/40',
        colSpan === 2 && 'col-span-2',
      )}
    >
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-wider text-slate-500 font-medium mb-1">
        {Icon && <Icon size={11} />}
        {label}
      </div>
      <p className="text-sm text-slate-800 font-medium">{value}</p>
    </div>
  );
}

function ResearchStat({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-2xl font-semibold tabular-nums">{value}</p>
      <p className="text-[10px] uppercase tracking-wider opacity-70 mt-0.5">{label}</p>
    </div>
  );
}

function Section({ title, count, children }: { title: string; count?: number; children: React.ReactNode }) {
  return (
    <div>
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
        {count !== undefined && (
          <span className="text-xs text-slate-400 tabular-nums">{count}</span>
        )}
      </div>
      {children}
    </div>
  );
}

/* ─── Match panel ──────────────────────────────────────────────────────── */

function MatchPanel({ filters }: { filters: ProfessorFilters | null }) {
  const { showToast } = useToast();
  const [open, setOpen] = useState(false);
  const [specialty, setSpecialty] = useState('');
  const [department, setDepartment] = useState<string>('');
  const [running, setRunning] = useState(false);
  const [results, setResults] = useState<MatchCandidate[] | null>(null);
  const [query, setQuery] = useState<string | null>(null);

  const runMatch = async () => {
    const trimmed = specialty.trim();
    if (!trimmed) return;
    setRunning(true);
    try {
      const res = await professorsApi.match({
        specialty: trimmed,
        department_code: department || null,
        max_results: 5,
      });
      setResults(res.candidates);
      setQuery(res.query);
      if (res.candidates.length === 0) {
        showToast('Aucun enseignant ne correspond à cette spécialité.', 'info');
      }
    } catch (err) {
      const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
      showToast(`Recherche échouée — ${msg}`, 'error');
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-3 px-5 py-3 hover:bg-slate-50/60 transition-colors duration-100"
      >
        <div className="w-8 h-8 rounded-md bg-amber-50 text-amber-600 flex items-center justify-center">
          <Sparkles size={16} />
        </div>
        <div className="flex-1 text-left">
          <p className="text-sm font-semibold text-slate-900">
            Trouver un enseignant pour un module
          </p>
          <p className="text-xs text-slate-500">
            Saisissez la spécialité du cours — l'algorithme classe les candidats par
            similarité, h-index et capacité.
          </p>
        </div>
        <ChevronDown
          size={16}
          className={cn(
            'text-slate-400 transition-transform duration-200',
            open && 'rotate-180',
          )}
        />
      </button>

      {open && (
        <div className="border-t border-slate-200 p-5 space-y-4 bg-slate-50/40">
          <div className="grid grid-cols-1 sm:grid-cols-[1fr_auto_auto] gap-3">
            <input
              type="text"
              placeholder="ex. Machine Learning, Réseaux, Traitement du signal…"
              className="bg-white border border-slate-200 rounded-md px-3 py-2 text-sm outline-none focus:border-blue-700 placeholder:text-slate-400"
              value={specialty}
              onChange={(e) => setSpecialty(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter') void runMatch();
              }}
            />
            <select
              value={department}
              onChange={(e) => setDepartment(e.target.value)}
              className="bg-white border border-slate-200 rounded-md px-3 py-2 text-sm text-slate-700 outline-none focus:border-blue-700"
            >
              <option value="">Tous départements</option>
              {(filters?.departments ?? []).map((d) => (
                <option key={d.code} value={d.code}>
                  {d.code}
                </option>
              ))}
            </select>
            <button
              onClick={() => void runMatch()}
              disabled={running || !specialty.trim()}
              className="px-4 py-2 bg-[#1d5394] text-white text-sm font-semibold rounded-md hover:bg-[#153d6e] disabled:bg-slate-300 disabled:cursor-not-allowed transition-colors duration-150 inline-flex items-center justify-center gap-2"
            >
              {running ? <Loader2 size={14} className="animate-spin" /> : <Sparkles size={14} />}
              Classer
            </button>
          </div>

          {results !== null && (
            <div>
              {results.length === 0 ? (
                <p className="text-sm text-slate-500 italic text-center py-4">
                  Aucun enseignant ne correspond à « {query} ».
                </p>
              ) : (
                <ul className="space-y-2">
                  {results.map((c, i) => (
                    <MatchResultRow key={c.professor.id} candidate={c} rank={i + 1} />
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function MatchResultRow({ candidate, rank }: { candidate: MatchCandidate; rank: number }) {
  const p = candidate.professor;
  const pct = Math.round(candidate.score * 100);
  return (
    <li className="bg-white border border-slate-200 rounded-md p-3 flex items-center gap-3">
      <div className="text-xs font-mono text-slate-400 tabular-nums w-6 text-center shrink-0">
        #{rank}
      </div>
      <Avatar p={p} />
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-slate-900 truncate">
          {fullName(p)}
        </p>
        <p className="text-xs text-slate-500 truncate">
          {p.rank} · {p.primary_specialty ?? '—'}
        </p>
        {candidate.matched_terms.length > 0 && (
          <p className="text-[10px] text-slate-400 mt-0.5">
            Correspondance:{' '}
            {candidate.matched_terms.map((t, i) => (
              <span key={i} className="inline-block bg-amber-50 text-amber-700 px-1 py-0.5 rounded mr-1">
                {t}
              </span>
            ))}
          </p>
        )}
      </div>
      <div className="text-right shrink-0">
        <div className="flex items-center gap-1.5">
          <HIndexCell value={p.h_index} />
        </div>
      </div>
      <div className="w-28 shrink-0">
        <ScoreBar pct={pct} />
        <p className="text-[10px] text-slate-400 mt-0.5 text-right tabular-nums">
          score {candidate.score.toFixed(2)}
        </p>
      </div>
    </li>
  );
}

function ScoreBar({ pct }: { pct: number }) {
  const color = pct >= 70 ? 'bg-emerald-500' : pct >= 40 ? 'bg-blue-600' : 'bg-amber-500';
  return (
    <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
      <div
        className={cn('h-full transition-all duration-500', color)}
        style={{ width: `${Math.min(pct, 100)}%` }}
      />
    </div>
  );
}
