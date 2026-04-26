import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  Layers,
  Sparkles,
  Trash2,
  ChevronRight,
  Plus,
  RefreshCw,
} from 'lucide-react';
import { cn } from '@/src/lib/utils';
import {
  ApiError,
  ApplyTemplateResult,
  ImportStatus,
  IngestionImportStatus,
  MatchSuggestion,
  TemplateMatchResponse,
  TemplateSummary,
  ingestionApi,
} from '@/src/lib/api';
import { useToast } from '@/src/components/ui/Toast';

/* ─── Constants ────────────────────────────────────────────────────────── */

const DOMAINS: { value: string; label: string }[] = [
  { value: 'academic', label: 'Académique' },
  { value: 'finance', label: 'Finance' },
  { value: 'operational', label: 'Opérationnel (RH)' },
  { value: 'environmental', label: 'Environnemental' },
];

// The current single-tenant deployment uses a fixed institution UUID.
// Replace with `useAppStore` selection once multi-tenant lands.
const DEFAULT_INSTITUTION_ID = '00000000-0000-0000-0000-000000000001';

const STATUS_LABELS: Record<IngestionImportStatus, { label: string; tone: string }> = {
  pending:           { label: 'En attente',          tone: 'bg-slate-100 text-slate-600' },
  extracted:         { label: 'Extrait',             tone: 'bg-blue-50 text-blue-700' },
  mapping_proposed:  { label: 'Mapping proposé',     tone: 'bg-amber-50 text-amber-700' },
  mapping_confirmed: { label: 'Mapping confirmé',    tone: 'bg-violet-50 text-violet-700' },
  validated:         { label: 'Validé',              tone: 'bg-emerald-50 text-emerald-700' },
  committed:         { label: 'Engagé',              tone: 'bg-emerald-100 text-emerald-800' },
  cancelled:         { label: 'Annulé',              tone: 'bg-red-50 text-red-700' },
};

const FORMAT_FROM_FILE: Record<string, string> = {
  xlsx: 'xlsx',
  xls:  'xlsx',
  csv:  'csv',
  pdf:  'pdf',
  png:  'image',
  jpg:  'image',
  jpeg: 'image',
  tiff: 'image',
  webp: 'image',
};

function detectFormat(filename: string): string {
  const ext = filename.split('.').pop()?.toLowerCase() ?? '';
  return FORMAT_FROM_FILE[ext] ?? 'csv';
}

/* ─── Page ─────────────────────────────────────────────────────────────── */

type ActiveImport = {
  status: ImportStatus;
  match?: TemplateMatchResponse | null;
  applied?: ApplyTemplateResult;
};

export function Ingestion() {
  const { showToast } = useToast();
  const [domain, setDomain] = useState<string>('academic');
  const [period, setPeriod] = useState<string>(`${new Date().getFullYear()}-S1`);
  const [active, setActive] = useState<ActiveImport | null>(null);
  const [uploading, setUploading] = useState(false);
  const [templates, setTemplates] = useState<TemplateSummary[]>([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [savingTemplate, setSavingTemplate] = useState(false);
  const [templateNameDraft, setTemplateNameDraft] = useState('');
  const [committing, setCommitting] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const [pickedFile, setPickedFile] = useState<File | null>(null);
  const pollRef = useRef<number | null>(null);

  const reloadTemplates = useCallback(async () => {
    setTemplatesLoading(true);
    try {
      const list = await ingestionApi.listTemplates({
        institution_id: DEFAULT_INSTITUTION_ID,
      });
      setTemplates(list);
    } catch (err) {
      const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
      setError(msg);
    } finally {
      setTemplatesLoading(false);
    }
  }, []);

  useEffect(() => {
    void reloadTemplates();
  }, [reloadTemplates]);

  // Stop any pending poller when active import changes / unmounts.
  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearTimeout(pollRef.current);
    };
  }, []);

  const startPolling = useCallback(
    (importId: string) => {
      let attempts = 0;
      const tick = async () => {
        attempts += 1;
        try {
          const status = await ingestionApi.importStatus(importId);
          setActive((prev) => (prev ? { ...prev, status } : { status }));
          if (
            status.status === 'extracted' &&
            status.headers &&
            status.headers.length > 0
          ) {
            // Run template matcher once we have headers.
            const fmt = status.headers
              ? detectFormat(status.original_filename)
              : 'csv';
            const match = await ingestionApi.matchTemplates({
              institution_id: DEFAULT_INSTITUTION_ID,
              headers: status.headers,
              source_format: fmt,
              domain: status.domain ?? undefined,
            });
            setActive((prev) =>
              prev ? { ...prev, status, match } : { status, match },
            );
            // Auto-apply the best match if confidence is high enough.
            if (match.best?.auto_confirm) {
              const applied = await ingestionApi.applyTemplate(
                status.import_id,
                match.best.template.id,
              );
              setActive((prev) =>
                prev
                  ? { ...prev, applied }
                  : { status, match, applied },
              );
              showToast(
                `Modèle « ${match.best.template.name} » appliqué automatiquement (score ${(match.best.score * 100).toFixed(0)}%)`,
                'success',
              );
            }
            return; // stop polling — UI will drive next step
          }
          if (
            status.status === 'mapping_confirmed' ||
            status.status === 'validated'
          ) {
            return;
          }
          if (status.status === 'committed' || status.status === 'cancelled') {
            return;
          }
        } catch (err) {
          const msg = err instanceof ApiError ? `${err.status} ${err.statusText}` : String(err);
          setError(`Polling: ${msg}`);
          return;
        }
        // Re-schedule with backoff: 600ms initially, capped at 3s.
        const delay = Math.min(600 + attempts * 200, 3000);
        pollRef.current = window.setTimeout(tick, delay);
      };
      void tick();
    },
    [showToast],
  );

  const handleUpload = async () => {
    if (!pickedFile) {
      showToast('Sélectionnez un fichier avant de téléverser.', 'warning');
      return;
    }
    setUploading(true);
    setError(null);
    setActive(null);
    try {
      const result = await ingestionApi.upload({
        file: pickedFile,
        institutionId: DEFAULT_INSTITUTION_ID,
        domain,
        period,
      });
      const initial: ImportStatus = {
        import_id: result.import_id,
        status: result.status,
        domain,
        period,
        original_filename: pickedFile.name,
        created_at: new Date().toISOString(),
      };
      setActive({ status: initial });
      startPolling(result.import_id);
      showToast(`Fichier reçu — ${pickedFile.name}`, 'info');
    } catch (err) {
      const msg = err instanceof ApiError ? errorMessage(err) : String(err);
      setError(msg);
      showToast(`Échec — ${msg}`, 'error');
    } finally {
      setUploading(false);
    }
  };

  const handleApplyTemplate = async (suggestion: MatchSuggestion) => {
    if (!active) return;
    try {
      const applied = await ingestionApi.applyTemplate(
        active.status.import_id,
        suggestion.template.id,
      );
      const refreshed = await ingestionApi.importStatus(active.status.import_id);
      setActive({ status: refreshed, match: active.match, applied });
      showToast(`Modèle appliqué — ${suggestion.template.name}`, 'success');
    } catch (err) {
      showToast(`Application échouée — ${errorMessage(err)}`, 'error');
    }
  };

  const handleCreateTemplate = async () => {
    if (!active) return;
    const code = templateNameDraft.trim();
    if (!code) {
      showToast('Donnez un nom au modèle.', 'warning');
      return;
    }
    setSavingTemplate(true);
    try {
      await ingestionApi.createTemplate({
        import_id: active.status.import_id,
        code,
        name: code,
      });
      showToast('Modèle enregistré.', 'success');
      setTemplateNameDraft('');
      await reloadTemplates();
    } catch (err) {
      showToast(`Création échouée — ${errorMessage(err)}`, 'error');
    } finally {
      setSavingTemplate(false);
    }
  };

  const handleCommit = async () => {
    if (!active) return;
    setCommitting(true);
    try {
      const result = await ingestionApi.commit(active.status.import_id, 'merge');
      const refreshed = await ingestionApi.importStatus(active.status.import_id);
      setActive({ status: refreshed, match: active.match, applied: active.applied });
      showToast(
        `${result.records_committed} enregistrements engagés. Recalcul des KPIs lancé.`,
        'success',
      );
    } catch (err) {
      showToast(`Commit échoué — ${errorMessage(err)}`, 'error');
    } finally {
      setCommitting(false);
    }
  };

  const handleCancel = async () => {
    if (!active) return;
    try {
      await ingestionApi.cancel(active.status.import_id);
      setActive(null);
      showToast('Import annulé.', 'info');
    } catch (err) {
      showToast(`Annulation échouée — ${errorMessage(err)}`, 'error');
    }
  };

  const handleDeleteTemplate = async (id: string, name: string) => {
    if (!confirm(`Archiver le modèle « ${name} » ?`)) return;
    try {
      await ingestionApi.deleteTemplate(id);
      showToast('Modèle archivé.', 'info');
      await reloadTemplates();
    } catch (err) {
      showToast(`Archivage échoué — ${errorMessage(err)}`, 'error');
    }
  };

  const onPickFile = (file: File | null) => {
    setPickedFile(file);
  };

  const stepLabel = useMemo(() => {
    if (!active) return null;
    if (active.applied) return 'Mapping appliqué — prêt à valider';
    const s = active.status.status;
    if (s === 'pending') return 'Réception du fichier…';
    if (s === 'extracted') return active.match ? 'Extraction terminée — modèle proposé' : 'Extraction terminée';
    if (s === 'mapping_proposed') return 'Mapping en cours de proposition';
    if (s === 'mapping_confirmed') return 'Mapping confirmé — validation en cours';
    if (s === 'validated') return 'Validation OK — prêt à engager';
    if (s === 'committed') return 'Données engagées';
    if (s === 'cancelled') return 'Import annulé';
    return null;
  }, [active]);

  return (
    <div className="space-y-6">
      {/* Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-end justify-between flex-wrap gap-3">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <UploadCloud size={22} className="text-blue-800" />
            <h1 className="text-xl font-semibold text-slate-900">
              Téléversement de données
            </h1>
          </div>
          <p className="text-sm text-slate-500 pl-[34px]">
            Importez Excel, CSV, PDF ou images. Sauvegardez les mappings comme modèles
            réutilisables pour des téléversements de masse en un clic.
          </p>
        </div>
        <button
          onClick={() => void reloadTemplates()}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-slate-900 px-2.5 py-1.5 rounded-md border border-slate-200 bg-white hover:border-slate-300 transition-colors duration-150"
          title="Recharger les modèles"
        >
          <RefreshCw size={13} className={cn(templatesLoading && 'animate-spin')} />
          Modèles
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 text-sm rounded-md px-4 py-2">
          {error}
        </div>
      )}

      {/* Upload card ─────────────────────────────────────────────────────── */}
      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
        <div className="p-5 grid grid-cols-1 lg:grid-cols-[1fr_auto_auto] gap-3">
          <div className="grid grid-cols-2 gap-3">
            <FilterPicker
              label="Domaine"
              value={domain}
              onChange={setDomain}
              options={DOMAINS}
            />
            <div>
              <label className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
                Période
              </label>
              <input
                type="text"
                value={period}
                onChange={(e) => setPeriod(e.target.value)}
                placeholder="2026-S1"
                className="mt-1 w-full bg-white border border-slate-200 rounded-md px-3 py-2 text-sm outline-none focus:border-blue-700"
              />
            </div>
          </div>
          <div className="flex items-end">
            <button
              onClick={() => fileInput.current?.click()}
              className="px-4 py-2 text-sm font-medium border border-slate-200 rounded-md hover:bg-slate-50 transition-colors duration-150 text-slate-700"
            >
              Choisir un fichier
            </button>
            <input
              ref={fileInput}
              type="file"
              hidden
              accept=".xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg,.tiff,.webp,application/pdf,image/*"
              onChange={(e) => onPickFile(e.target.files?.[0] ?? null)}
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => void handleUpload()}
              disabled={uploading || !pickedFile}
              className="px-4 py-2 bg-[#1d5394] text-white text-sm font-semibold rounded-md hover:bg-[#153d6e] disabled:bg-slate-300 disabled:cursor-not-allowed inline-flex items-center justify-center gap-2"
            >
              {uploading ? <Loader2 size={14} className="animate-spin" /> : <UploadCloud size={14} />}
              Téléverser
            </button>
          </div>
        </div>

        {/* Drop zone */}
        <DropZone file={pickedFile} onPick={onPickFile} />
      </div>

      {/* Active import flow ──────────────────────────────────────────────── */}
      {active && (
        <ActiveImportCard
          active={active}
          stepLabel={stepLabel}
          committing={committing}
          savingTemplate={savingTemplate}
          templateNameDraft={templateNameDraft}
          onTemplateNameChange={setTemplateNameDraft}
          onCommit={() => void handleCommit()}
          onCancel={() => void handleCancel()}
          onCreateTemplate={() => void handleCreateTemplate()}
          onApplyTemplate={(s) => void handleApplyTemplate(s)}
        />
      )}

      {/* Templates gallery ──────────────────────────────────────────────── */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
            <Layers size={15} className="text-slate-500" />
            Modèles enregistrés
          </h2>
          <span className="text-xs text-slate-400">
            {templates.length} modèle{templates.length > 1 ? 's' : ''}
          </span>
        </div>
        {templates.length === 0 ? (
          <EmptyTemplatesHint />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-3">
            {templates.map((t) => (
              <TemplateCard
                key={t.id}
                template={t}
                onDelete={() => void handleDeleteTemplate(t.id, t.name)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Drop zone ────────────────────────────────────────────────────────── */

function DropZone({
  file,
  onPick,
}: {
  file: File | null;
  onPick: (f: File | null) => void;
}) {
  const [over, setOver] = useState(false);
  return (
    <label
      onDragOver={(e) => {
        e.preventDefault();
        setOver(true);
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault();
        setOver(false);
        if (e.dataTransfer.files[0]) onPick(e.dataTransfer.files[0]);
      }}
      className={cn(
        'block border-t border-dashed border-slate-200 px-6 py-8 transition-colors duration-150',
        over ? 'bg-blue-50/40' : 'bg-slate-50/40',
      )}
    >
      <input
        type="file"
        hidden
        accept=".xlsx,.xls,.csv,.pdf,.png,.jpg,.jpeg,.tiff,.webp,application/pdf,image/*"
        onChange={(e) => onPick(e.target.files?.[0] ?? null)}
      />
      <div className="flex items-center gap-4 max-w-xl mx-auto">
        <div className="w-10 h-10 rounded-full bg-white shadow-sm flex items-center justify-center shrink-0">
          <UploadCloud size={20} className="text-slate-400" />
        </div>
        <div className="flex-1 min-w-0">
          {file ? (
            <>
              <p className="text-sm font-medium text-slate-900 truncate">{file.name}</p>
              <p className="text-xs text-slate-500">
                {(file.size / 1024).toLocaleString('fr-FR', {
                  maximumFractionDigits: 0,
                })}{' '}
                Ko · {file.type || 'type inconnu'}
              </p>
            </>
          ) : (
            <>
              <p className="text-sm font-medium text-slate-700">
                Glissez-déposez un fichier ici, ou utilisez « Choisir un fichier ».
              </p>
              <p className="text-xs text-slate-400">
                Formats : XLSX, CSV, PDF, PNG, JPG · max 50 Mo.
              </p>
            </>
          )}
        </div>
        {file && (
          <button
            onClick={(e) => {
              e.preventDefault();
              onPick(null);
            }}
            className="p-1 text-slate-400 hover:text-slate-600"
            title="Retirer"
          >
            <X size={16} />
          </button>
        )}
      </div>
    </label>
  );
}

/* ─── Active import card ───────────────────────────────────────────────── */

function ActiveImportCard({
  active,
  stepLabel,
  committing,
  savingTemplate,
  templateNameDraft,
  onTemplateNameChange,
  onCommit,
  onCancel,
  onCreateTemplate,
  onApplyTemplate,
}: {
  active: ActiveImport;
  stepLabel: string | null;
  committing: boolean;
  savingTemplate: boolean;
  templateNameDraft: string;
  onTemplateNameChange: (v: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  onCreateTemplate: () => void;
  onApplyTemplate: (s: MatchSuggestion) => void;
}) {
  const status = active.status.status;
  const meta = STATUS_LABELS[status] ?? STATUS_LABELS.pending;
  const headers = active.status.headers ?? [];
  const matchedSet = new Set(active.applied
    ? Object.keys(active.applied.confirmed_mapping ?? {}).filter(
        (k) => active.applied!.confirmed_mapping![k],
      )
    : []);

  const isFinal = status === 'committed' || status === 'cancelled';
  const canCommit = status === 'mapping_confirmed' || status === 'validated';
  const canSaveAsTemplate =
    !!active.applied || status === 'mapping_confirmed' || status === 'validated';

  return (
    <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-slate-200 flex items-center justify-between gap-3 flex-wrap">
        <div className="flex items-center gap-3 min-w-0">
          <FileText size={18} className="text-slate-500 shrink-0" />
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate">
              {active.status.original_filename}
            </p>
            <p className="text-xs text-slate-500">
              {active.status.domain ?? '—'} · {active.status.period ?? '—'} ·
              {headers.length > 0 ? ` ${headers.length} colonnes` : ' extraction…'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              'text-xs font-medium px-2 py-0.5 rounded-md',
              meta.tone,
            )}
          >
            {meta.label}
          </span>
          {!isFinal && (
            <button
              onClick={onCancel}
              className="text-xs text-slate-500 hover:text-red-600"
              title="Annuler l'import"
            >
              <X size={14} />
            </button>
          )}
        </div>
      </div>

      {/* Step label */}
      {stepLabel && (
        <div className="px-5 py-2.5 border-b border-slate-200 bg-slate-50/40 text-xs text-slate-600 flex items-center gap-2">
          {(status === 'pending' || status === 'mapping_proposed') ? (
            <Loader2 size={12} className="animate-spin text-blue-700" />
          ) : (
            <ChevronRight size={12} className="text-slate-400" />
          )}
          {stepLabel}
        </div>
      )}

      {/* Match suggestions ─────────────────────────────────────────────── */}
      {status === 'extracted' && active.match && active.match.suggestions.length > 0 && !active.applied && (
        <div className="p-5 space-y-2 bg-amber-50/40 border-b border-slate-200">
          <p className="text-sm font-semibold text-slate-900 flex items-center gap-1.5">
            <Sparkles size={14} className="text-amber-600" />
            Modèles correspondants
          </p>
          <ul className="space-y-2">
            {active.match.suggestions.map((s) => (
              <SuggestionRow
                key={s.template.id}
                suggestion={s}
                onApply={() => onApplyTemplate(s)}
              />
            ))}
          </ul>
        </div>
      )}

      {/* No match — fallback explanation */}
      {status === 'extracted' && active.match && active.match.suggestions.length === 0 && !active.applied && (
        <div className="p-5 bg-slate-50/40 border-b border-slate-200">
          <p className="text-sm text-slate-700">
            Aucun modèle existant ne correspond aux entêtes de ce fichier.
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Confirmez le mapping manuellement via l'API <code>/imports/{'{id}'}/mapping</code>{' '}
            puis revenez ici pour engager.
          </p>
        </div>
      )}

      {/* Applied template recap */}
      {active.applied && (
        <div className="p-5 bg-emerald-50/40 border-b border-slate-200">
          <p className="text-sm font-semibold text-emerald-800 flex items-center gap-1.5">
            <CheckCircle2 size={14} />
            Mapping appliqué
          </p>
          <p className="text-xs text-slate-600 mt-1">
            {Object.values(active.applied.confirmed_mapping || {}).filter(Boolean).length}{' '}
            colonne(s) sur {Object.keys(active.applied.confirmed_mapping || {}).length} mappée(s)
            vers le registre KPI.
          </p>
        </div>
      )}

      {/* Headers preview */}
      {headers.length > 0 && (
        <div className="p-5 border-b border-slate-200">
          <p className="text-[10px] uppercase tracking-wider text-slate-500 font-medium mb-2">
            Colonnes détectées
          </p>
          <div className="flex flex-wrap gap-1.5">
            {headers.map((h) => {
              const matched = matchedSet.has(h);
              return (
                <span
                  key={h}
                  className={cn(
                    'inline-flex items-center text-[11px] px-2 py-0.5 rounded-md border',
                    matched
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200/60'
                      : 'bg-slate-50 text-slate-700 border-slate-200/60',
                  )}
                >
                  {matched && <CheckCircle2 size={10} className="mr-1" />}
                  {h}
                </span>
              );
            })}
          </div>
        </div>
      )}

      {/* Bottom action bar */}
      <div className="px-5 py-3 bg-slate-50/40 flex items-center justify-between flex-wrap gap-3">
        {canSaveAsTemplate ? (
          <div className="flex items-center gap-2">
            <input
              type="text"
              value={templateNameDraft}
              onChange={(e) => onTemplateNameChange(e.target.value)}
              placeholder="Nom du modèle (ex. roster-faculté)"
              className="bg-white border border-slate-200 rounded-md px-3 py-1.5 text-sm outline-none focus:border-blue-700 placeholder:text-slate-400"
            />
            <button
              onClick={onCreateTemplate}
              disabled={savingTemplate || !templateNameDraft.trim()}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium border border-slate-200 rounded-md bg-white hover:border-slate-300 disabled:opacity-50"
            >
              {savingTemplate ? <Loader2 size={13} className="animate-spin" /> : <Plus size={13} />}
              Sauvegarder le mapping
            </button>
          </div>
        ) : (
          <span />
        )}
        {canCommit && (
          <button
            onClick={onCommit}
            disabled={committing}
            className="px-4 py-1.5 bg-[#1d5394] text-white text-sm font-semibold rounded-md hover:bg-[#153d6e] disabled:bg-slate-300 inline-flex items-center justify-center gap-2"
          >
            {committing ? <Loader2 size={13} className="animate-spin" /> : <CheckCircle2 size={13} />}
            Engager les données
          </button>
        )}
      </div>
    </div>
  );
}

function SuggestionRow({
  suggestion,
  onApply,
}: {
  suggestion: MatchSuggestion;
  onApply: () => void;
}) {
  const pct = Math.round(suggestion.score * 100);
  const cov = Math.round(suggestion.header_coverage * 100);
  const tone =
    pct >= 70
      ? 'bg-emerald-500'
      : pct >= 50
        ? 'bg-blue-600'
        : 'bg-amber-500';
  return (
    <li className="bg-white border border-slate-200 rounded-md p-3 flex items-center gap-3">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-semibold text-slate-900 truncate">
            {suggestion.template.name}
          </p>
          {suggestion.auto_confirm && (
            <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-700 font-semibold">
              Auto
            </span>
          )}
        </div>
        <p className="text-xs text-slate-500 truncate">
          {suggestion.template.code} · {suggestion.matched_headers.length} colonne(s)
          en commun · couverture {cov}%
        </p>
      </div>
      <div className="w-28 shrink-0">
        <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={cn('h-full transition-all duration-500', tone)}
            style={{ width: `${pct}%` }}
          />
        </div>
        <p className="text-[10px] text-slate-400 mt-0.5 text-right tabular-nums">
          {pct}% similarité
        </p>
      </div>
      <button
        onClick={onApply}
        className="px-3 py-1.5 text-xs font-medium bg-[#1d5394] text-white rounded-md hover:bg-[#153d6e] shrink-0"
      >
        Appliquer
      </button>
    </li>
  );
}

/* ─── Templates gallery ────────────────────────────────────────────────── */

function TemplateCard({
  template,
  onDelete,
}: {
  template: TemplateSummary;
  onDelete: () => void;
}) {
  return (
    <div className="bg-white border border-slate-200 rounded-lg p-4 group hover:border-slate-300 transition-colors duration-150">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-sm font-semibold text-slate-900 truncate">{template.name}</p>
          <p className="text-xs text-slate-500 truncate font-mono">{template.code}</p>
        </div>
        <button
          onClick={onDelete}
          className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-600 transition-opacity duration-150"
          title="Archiver"
        >
          <Trash2 size={13} />
        </button>
      </div>
      <div className="flex items-center gap-2 mt-2">
        <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">
          {template.source_format}
        </span>
        <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 font-medium">
          {template.domain}
        </span>
      </div>
      <div className="mt-3 flex flex-wrap gap-1">
        {template.sample_headers.slice(0, 5).map((h) => (
          <span
            key={h}
            className="text-[10px] text-slate-600 bg-slate-50 border border-slate-200/80 px-1.5 py-0.5 rounded"
          >
            {h}
          </span>
        ))}
        {template.sample_headers.length > 5 && (
          <span className="text-[10px] text-slate-400">
            +{template.sample_headers.length - 5}
          </span>
        )}
      </div>
      <div className="mt-3 grid grid-cols-2 text-[11px] text-slate-500">
        <div>
          <span className="block text-[9px] uppercase tracking-wider text-slate-400">
            Champs mappés
          </span>
          <span className="font-semibold text-slate-700 tabular-nums">
            {template.mapped_field_count}/{template.field_count}
          </span>
        </div>
        <div className="text-right">
          <span className="block text-[9px] uppercase tracking-wider text-slate-400">
            Utilisations
          </span>
          <span className="font-semibold text-slate-700 tabular-nums">
            {template.match_count}
          </span>
        </div>
      </div>
    </div>
  );
}

function EmptyTemplatesHint() {
  return (
    <div className="bg-white border border-dashed border-slate-200 rounded-lg p-6 text-center text-sm text-slate-500">
      <Layers size={20} className="mx-auto mb-2 text-slate-300" />
      Aucun modèle pour l'instant. Téléversez un premier fichier, confirmez son mapping,
      puis cliquez « Sauvegarder le mapping » pour le réutiliser sur les fichiers suivants.
    </div>
  );
}

/* ─── Misc ──────────────────────────────────────────────────────────────── */

function FilterPicker({
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
    <div>
      <label className="text-[10px] uppercase tracking-wider text-slate-500 font-medium">
        {label}
      </label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 w-full bg-white border border-slate-200 rounded-md px-3 py-2 text-sm text-slate-700 outline-none focus:border-blue-700"
      >
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

function errorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    const body = err.body as { detail?: string } | null;
    return body?.detail ?? `${err.status} ${err.statusText}`;
  }
  return String(err);
}

// Silence unused import warning
void AlertCircle;
