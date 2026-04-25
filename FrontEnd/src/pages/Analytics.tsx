import { LineChart, Filter } from "lucide-react";
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

const colors = ['#1d4ed8', '#334155', '#0f766e', '#b45309', '#be123c'];

export function Analytics() {
  const [selectedKpi, setSelectedKpi] = useState('Taux de réussite');
  const [selectedInsts, setSelectedInsts] = useState<string[]>(['INSAT', 'EPT', 'ENSTAB']);

  return (
    <div className="space-y-6">
      <div>
        <div>
          <h2 className="text-xl font-semibold text-slate-900">Explorateur KPI</h2>
          <p className="text-sm text-slate-600 mt-1">Comparaison des performances entre etablissements</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-1 space-y-6 bg-white p-5 rounded-md border border-slate-200 h-fit">
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
              <Filter size={14} /> Configuration
            </h3>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Indicateur KPI</label>
              <select 
                className="w-full bg-slate-50 border border-slate-300 rounded-md px-3 py-2 text-sm outline-none focus:border-blue-700"
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
              <label className="text-sm font-medium text-slate-700">Etablissements ({selectedInsts.length})</label>
              <div className="flex flex-wrap gap-2">
                {selectedInsts.map(code => (
                  <span key={code} className="bg-slate-100 text-slate-700 px-2 py-1 rounded text-xs font-medium flex items-center gap-1.5 border border-slate-200">
                    {code}
                    <button onClick={() => setSelectedInsts(prev => prev.filter(c => c !== code))} className="hover:text-red-700">x</button>
                  </span>
                ))}
              </div>
              <div className="pt-2 h-40 overflow-y-auto space-y-1 pr-1">
                {institutionsData.map(inst => (
                  <button
                    key={inst.code}
                    onClick={() => {
                      if (!selectedInsts.includes(inst.code)) setSelectedInsts([...selectedInsts, inst.code]);
                    }}
                    className={cn(
                      'w-full text-left px-3 py-1.5 rounded text-sm transition-colors duration-150',
                      selectedInsts.includes(inst.code) ? 'bg-slate-100 text-slate-400 cursor-not-allowed' : 'hover:bg-slate-100 text-slate-700'
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

        <div className="lg:col-span-3 space-y-6">
          <div className="bg-white p-6 rounded-md border border-slate-200">
            <div className="flex justify-between items-center mb-6">
              <div>
                <h3 className="text-base font-semibold text-slate-900 capitalize">{selectedKpi}</h3>
                <p className="text-sm text-slate-600 mt-1">Comparaison des 3 derniers semestres</p>
              </div>
              <div className="p-2 bg-slate-100 text-slate-700 rounded">
                 <LineChart size={24} />
              </div>
            </div>

            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ReLineChart data={mockComparison}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#E2E8F0" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: '#475569' }} unit="%" />
                  <Tooltip 
                    contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1', boxShadow: 'none' }}
                  />
                  <Legend 
                    verticalAlign="top" 
                    align="right" 
                    iconType="circle" 
                    wrapperStyle={{ paddingTop: 0, paddingBottom: 20 }}
                    formatter={(value) => <span className="text-xs font-medium text-slate-700 pr-4">{value}</span>}
                  />
                  {selectedInsts.map((code, idx) => (
                    <Line 
                      key={code}
                      type="monotone" 
                      dataKey={code} 
                      stroke={colors[idx % colors.length]} 
                      strokeWidth={2}
                      dot={{ r: 3, strokeWidth: 0, fill: colors[idx % colors.length] }}
                      activeDot={{ r: 4, strokeWidth: 0 }}
                      isAnimationActive={false}
                    />
                  ))}
                </ReLineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="bg-white rounded-md border border-slate-200 overflow-hidden">
             <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200">
                  <tr>
                    <th className="px-6 py-3 text-xs font-semibold text-slate-700">Etablissement</th>
                    <th className="px-6 py-3 text-xs font-semibold text-slate-700 text-center">Valeur actuelle</th>
                    <th className="px-6 py-3 text-xs font-semibold text-slate-700 text-right">Ecart moyenne reseau</th>
                  </tr>
                </thead>
                <tbody>
                  {selectedInsts.map(code => (
                    <tr key={code} className="border-b border-slate-200 last:border-0 hover:bg-slate-50">
                      <td className="px-6 py-4 font-medium text-sm text-slate-900 uppercase">{code}</td>
                      <td className="px-6 py-4 text-center font-medium font-tabular text-sm text-slate-800">79.2%</td>
                      <td className="px-6 py-4 text-right">
                        <span className="text-xs font-medium text-green-700">+2.4%</span>
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
