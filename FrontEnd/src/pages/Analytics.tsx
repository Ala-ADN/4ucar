import { useState } from 'react';
import { Download, FileText, Search, Calendar, Sheet, Sparkles, CheckCircle2 } from 'lucide-react';
import { cn } from '@/src/lib/utils';

/* ─── Mock Report Data ─── */

interface Report {
  id: string;
  name: string;
  aiSummary: string;
  period: string;
  generatedAt: string;
  generatedBy: string;
  format: 'PDF' | 'XLSX' | 'CSV';
  category: string;
  size: string;
  readStatus: 'Lu' | 'Non lu';
}

const reports: Report[] = [
  { 
    id: 'RPT-001', 
    name: 'Synthèse réseau — Indicateurs de Gouvernance', 
    aiSummary: 'Le taux de conformité documentaire a progressé de +1.2%. 3 faiblesses identifiées (FST, ENIT, IHEC).', 
    period: 'S1 2025-26', 
    generatedAt: '2026-04-20', 
    generatedBy: 'Système Auto',
    format: 'PDF', 
    category: 'Gouvernance', 
    size: '2.4 Mo',
    readStatus: 'Non lu'
  },
  { 
    id: 'RPT-002', 
    name: 'Exécution budgétaire trimestrielle', 
    aiSummary: 'Taux d\'exécution global à 72%. Risque de sous-consommation du Titre II (Investissement).', 
    period: 'T1 2026', 
    generatedAt: '2026-04-18', 
    generatedBy: 'Dr. Ammar (DAF)',
    format: 'XLSX', 
    category: 'Finance', 
    size: '1.8 Mo',
    readStatus: 'Lu'
  },
  { 
    id: 'RPT-003', 
    name: 'Audit interne ISO 9001 — Rapport des NC', 
    aiSummary: '14 non-conformités résolues. 2 majeures en attente de clôture (Processus RH).', 
    period: 'Mois de Mars', 
    generatedAt: '2026-04-15', 
    generatedBy: 'Cellule Qualité',
    format: 'PDF', 
    category: 'Accréditation', 
    size: '890 Ko',
    readStatus: 'Lu'
  },
  { 
    id: 'RPT-004', 
    name: 'Export données GreenMetric', 
    aiSummary: 'Données brutes prêtes pour la soumission. Conso. énergie -4% vs N-1.', 
    period: '2025-26', 
    generatedAt: '2026-04-10', 
    generatedBy: 'Système Auto',
    format: 'CSV', 
    category: 'Durabilité', 
    size: '420 Ko',
    readStatus: 'Non lu'
  },
];

/* ─── Format Badge ─── */

function FormatChip({ format }: { format: Report['format'] }) {
  const config: Record<string, { style: string; icon: typeof FileText }> = {
    PDF: { style: 'border-red-200 text-red-600 bg-red-50/60', icon: FileText },
    XLSX: { style: 'border-emerald-200 text-emerald-600 bg-emerald-50/60', icon: Sheet },
    CSV: { style: 'border-slate-200 text-slate-600 bg-slate-50', icon: FileText },
  };
  const c = config[format] || config.CSV;
  const Icon = c.icon;
  return (
    <span className={cn('inline-flex items-center gap-1 px-2 py-0.5 rounded border text-[10px] font-semibold uppercase tracking-wide', c.style)}>
      <Icon size={10} />
      {format}
    </span>
  );
}

/* ─── Main Component ─── */

export function Analytics() {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('all');

  const categories = [...new Set(reports.map((r) => r.category))];

  const filtered = reports.filter((r) => {
    const matchSearch = r.name.toLowerCase().includes(searchTerm.toLowerCase());
    const matchCategory = categoryFilter === 'all' || r.category === categoryFilter;
    return matchSearch && matchCategory;
  });

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl tracking-tight font-semibold text-[#0F172A]">Rapports & Synthèses IA</h2>
          <p className="text-sm text-slate-500 mt-1">Bibliothèque centralisée des documents officiels et synthèses intelligentes UCAR.</p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar size={14} className="text-slate-400" />
          <span className="text-xs text-slate-500">Mise à jour: 20 avr. 2026</span>
        </div>
      </div>

      {/* Filter Row */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-64 max-w-md">
          <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher (Nom du rapport, contenu...)"
            className="w-full bg-white border border-slate-200 rounded-lg pl-9 pr-4 py-2.5 text-sm outline-none focus:border-[#1d5394] placeholder:text-slate-400 transition-colors duration-100"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          className="appearance-none bg-white border border-slate-200 rounded-lg pl-4 pr-10 py-2.5 text-sm text-slate-700 outline-none focus:border-[#1d5394] cursor-pointer"
        >
          <option value="all">Toutes les catégories</option>
          {categories.map((c) => (
            <option key={c} value={c}>{c}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-left">
          <thead>
            <tr>
              <th className="py-4 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Document & Synthèse</th>
              <th className="py-4 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Généré par</th>
              <th className="py-4 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">Période</th>
              <th className="py-4 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">Format</th>
              <th className="py-4 px-6 text-[11px] font-semibold text-slate-500 uppercase tracking-wider text-center">Statut</th>
              <th className="py-4 px-6"></th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((report) => (
              <tr
                key={report.id}
                className="border-b border-slate-200/60 hover:bg-slate-50/50 transition-colors duration-200"
              >
                <td className="py-5 px-6">
                  <div className="flex flex-col gap-1.5">
                    <div className="flex items-center gap-2">
                       <span className="text-sm font-semibold text-[#0F172A] tracking-tight">{report.name}</span>
                       <span className="text-[10px] text-slate-400 tabular-nums uppercase border border-slate-200 rounded px-1.5">{report.id}</span>
                    </div>
                    <div className="flex items-start gap-1.5 mt-1">
                      <Sparkles size={13} className="text-[#1d5394] mt-0.5 shrink-0" />
                      <p className="text-[13px] text-slate-600 italic leading-relaxed max-w-2xl">{report.aiSummary}</p>
                    </div>
                  </div>
                </td>
                <td className="py-5 px-6">
                  <p className="text-sm font-medium text-slate-800">{report.generatedBy}</p>
                  <p className="text-xs text-slate-500 mt-0.5 tabular-nums">
                    {new Date(report.generatedAt).toLocaleDateString('fr-FR', { day: '2-digit', month: 'long', year: 'numeric' })}
                  </p>
                </td>
                <td className="py-5 px-6 text-sm text-slate-700">{report.period}</td>
                <td className="py-5 px-6 text-center">
                  <FormatChip format={report.format} />
                </td>
                <td className="py-5 px-6 text-center">
                  {report.readStatus === 'Lu' ? (
                     <span className="inline-flex items-center gap-1 text-[11px] font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full">
                       <CheckCircle2 size={12} /> Lu
                     </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-700 bg-amber-50 px-2 py-0.5 rounded-full">
                       <div className="w-1.5 h-1.5 rounded-full bg-amber-500" /> Non lu
                    </span>
                  )}
                </td>
                <td className="py-5 px-6 text-right">
                  <button className="flex items-center gap-2 px-3 py-1.5 text-xs font-semibold text-[#1d5394] bg-[#F0F5FA] hover:bg-[#E8EFF6] rounded-md transition-colors duration-150">
                    <Download size={14} />
                    <span>{report.size}</span>
                  </button>
                </td>
              </tr>
            ))}

            {filtered.length === 0 && (
              <tr>
                <td colSpan={6} className="py-20 text-center">
                   <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-3">
                     <Search size={20} className="text-slate-400" />
                   </div>
                  <p className="text-sm font-medium text-slate-600">Aucun rapport ne correspond à votre recherche.</p>
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
