import { BarChart3, LineChart, PieChart, Info, Filter } from "lucide-react";
import { motion } from "motion/react";
import { useState } from "react";
import institutionsData from "@/src/data/institutions.json";
import { cn } from "@/src/lib/utils";
import { 
  LineChart as ReLineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend
} from 'recharts';

const kpiOptions = [
  { group: 'Académique', items: ['Taux de réussite', 'Taux d\'abandon', 'Taux de redoublement'] },
  { group: 'Financier', items: ['Budget exécuté', 'Part masse salariale', 'Coût/étudiant'] },
  { group: 'RH', items: ['Taux d\'encadrement', 'Absentéisme', 'Taux vacataires'] },
];

const mockComparison = [
  { name: 'S1 23', INSAT: 78, EPT: 84, ENSTAB: 66 },
  { name: 'S2 23', INSAT: 79, EPT: 85, ENSTAB: 64 },
  { name: 'S1 24', INSAT: 79.2, EPT: 85.1, ENSTAB: 62.8 },
];

const colors = ['#3B82F6', '#6366F1', '#A855F7', '#EC4899', '#F97316'];

export function Analytics() {
  const [selectedKpi, setSelectedKpi] = useState('Taux de réussite');
  const [selectedInsts, setSelectedInsts] = useState<string[]>(['INSAT', 'EPT', 'ENSTAB']);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-xl font-bold text-text-primary uppercase tracking-tight">Explorateur KPI</h2>
          <p className="text-sm text-text-muted mt-1">Comparez les performances dynamiquement à travers le réseau</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Filters Panel */}
        <div className="lg:col-span-1 space-y-6 bg-surface p-6 rounded-2xl shadow-card border border-border h-fit">
          <div className="space-y-4">
            <h3 className="text-xs font-bold text-text-muted uppercase tracking-widest flex items-center gap-2">
              <Filter size={14} /> Configuration
            </h3>
            
            <div className="space-y-2">
              <label className="text-[11px] font-bold text-text-secondary">Indicateur KPI</label>
              <select 
                className="w-full bg-off-white border-none rounded-xl px-4 py-2.5 text-sm outline-none focus:ring-2 focus:ring-blue-500/20"
                value={selectedKpi}
                onChange={(e) => setSelectedKpi(e.target.value)}
              >
                {kpiOptions.map(group => (
                  <optgroup key={group.group} label={group.group}>
                    {group.items.map(item => (
                      <option key={item} value={item}>{item}</option>
                    ))}
                  </optgroup>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-[11px] font-bold text-text-secondary">Établissements ({selectedInsts.length})</label>
              <div className="flex flex-wrap gap-2">
                {selectedInsts.map(code => (
                  <span key={code} className="bg-blue-50 text-blue-700 px-2 py-1 rounded-lg text-[10px] font-bold flex items-center gap-1.5 border border-blue-100">
                    {code}
                    <button onClick={() => setSelectedInsts(prev => prev.filter(c => c !== code))} className="hover:text-status-critical">×</button>
                  </span>
                ))}
              </div>
              <div className="pt-2 h-40 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
                {institutionsData.map(inst => (
                  <button
                    key={inst.code}
                    onClick={() => {
                      if (!selectedInsts.includes(inst.code)) setSelectedInsts([...selectedInsts, inst.code]);
                    }}
                    className={cn(
                      "w-full text-left px-3 py-1.5 rounded-lg text-xs transition-colors",
                      selectedInsts.includes(inst.code) ? "bg-surface-hover text-text-muted opacity-50" : "hover:bg-off-white text-text-secondary"
                    )}
                    disabled={selectedInsts.includes(inst.code)}
                  >
                    {inst.code}
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Main Chart Area */}
        <div className="lg:col-span-3 space-y-6">
          <div className="bg-surface p-8 rounded-2xl shadow-card border border-border">
            <div className="flex justify-between items-center mb-12">
              <div>
                <h3 className="text-lg font-bold text-text-primary capitalize">{selectedKpi}</h3>
                <p className="text-xs text-text-muted mt-1">Comparaison des 3 derniers semestres</p>
              </div>
              <div className="p-3 bg-blue-50 text-blue-500 rounded-2xl">
                 <LineChart size={24} />
              </div>
            </div>

            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ReLineChart data={mockComparison}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 600 }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11 }} unit="%" />
                  <Tooltip 
                    contentStyle={{ borderRadius: '16px', border: 'none', boxShadow: '0 12px 24px rgba(0,0,0,0.1)' }}
                  />
                  <Legend 
                    verticalAlign="top" 
                    align="right" 
                    iconType="circle" 
                    wrapperStyle={{ paddingTop: 0, paddingBottom: 40 }}
                    formatter={(value) => <span className="text-xs font-bold text-text-secondary pr-4">{value}</span>}
                  />
                  {selectedInsts.map((code, idx) => (
                    <Line 
                      key={code}
                      type="monotone" 
                      dataKey={code} 
                      stroke={colors[idx % colors.length]} 
                      strokeWidth={4}
                      dot={{ r: 5, strokeWidth: 0, fill: colors[idx % colors.length] }}
                      activeDot={{ r: 8, strokeWidth: 0 }}
                      animationDuration={1000}
                    />
                  ))}
                </ReLineChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Comparison Table Small */}
          <div className="bg-surface rounded-2xl border border-border overflow-hidden">
             <table className="w-full text-left">
                <thead className="bg-off-white border-b border-border">
                  <tr>
                    <th className="px-6 py-4 text-[10px] font-bold text-text-muted uppercase tracking-widest">Établissement</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-text-muted uppercase tracking-widest text-center">Valeur Actuelle</th>
                    <th className="px-6 py-4 text-[10px] font-bold text-text-muted uppercase tracking-widest text-right">Écart Moyenne Réseau</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedInsts.map(code => (
                    <tr key={code} className="border-b border-border last:border-0">
                      <td className="px-6 py-4 font-bold text-sm text-text-primary uppercase">{code}</td>
                      <td className="px-6 py-4 text-center font-bold font-tabular text-sm text-text-secondary">79.2%</td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-xs font-bold text-status-good">+2.4%</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
             </table>
          </div>
        </div>
      </div>
    </div>
  );
}
