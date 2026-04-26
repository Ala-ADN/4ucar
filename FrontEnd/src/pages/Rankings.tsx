import institutionsData from '@/src/data/institutions.json';
import { Institution } from '@/src/types';

interface FinanceRow {
  code: string;
  name: string;
  budget_alloue_tnd: number;
  budget_execute_tnd: number;
  payroll_ratio: number;
  external_funding_tnd: number;
}

const financeRows: FinanceRow[] = [
  { code: 'EPT', name: 'Ecole Polytechnique de Tunisie', budget_alloue_tnd: 9100000, budget_execute_tnd: 7370000, payroll_ratio: 65.4, external_funding_tnd: 620000 },
  { code: 'INSAT', name: 'INSAT', budget_alloue_tnd: 8200000, budget_execute_tnd: 5576000, payroll_ratio: 71.2, external_funding_tnd: 320000 },
  { code: 'ENSTAB', name: 'ENSTAB', budget_alloue_tnd: 4200000, budget_execute_tnd: 1974000, payroll_ratio: 74.1, external_funding_tnd: 85000 },
  { code: 'FST', name: 'FST', budget_alloue_tnd: 15000000, budget_execute_tnd: 10950000, payroll_ratio: 69.1, external_funding_tnd: 470000 },
  { code: 'FSEG', name: 'FSEG', budget_alloue_tnd: 13600000, budget_execute_tnd: 10336000, payroll_ratio: 67.8, external_funding_tnd: 260000 },
];

export function Rankings() {
  const institutions = institutionsData as Institution[];
  const totalBudget = financeRows.reduce((acc, row) => acc + row.budget_alloue_tnd, 0);
  const totalExecuted = financeRows.reduce((acc, row) => acc + row.budget_execute_tnd, 0);
  const executionRate = ((totalExecuted / totalBudget) * 100).toFixed(1);
  const meanPayroll = (
    financeRows.reduce((acc, row) => acc + row.payroll_ratio, 0) / financeRows.length
  ).toFixed(1);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-slate-900">Suivi financier UCAR</h2>
        <p className="text-sm text-slate-600 mt-1">Execution budgetaire et soutenabilite par etablissement</p>
      </div>

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-sm text-slate-600">Budget reseau alloue</p>
          <p className="text-2xl font-semibold text-slate-900 mt-2">{Math.round(totalBudget / 1000000)} M TND</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-sm text-slate-600">Execution globale</p>
          <p className="text-2xl font-semibold text-slate-900 mt-2">{executionRate}%</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-sm text-slate-600">Masse salariale moyenne</p>
          <p className="text-2xl font-semibold text-slate-900 mt-2">{meanPayroll}%</p>
        </div>
      </section>

      <section className="bg-white border border-slate-200 rounded-md overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Etablissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Alloue (TND)</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Execute (TND)</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Execution</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Masse salariale</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Financement externe</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {financeRows.map((row) => {
              const execution = (row.budget_execute_tnd / row.budget_alloue_tnd) * 100;
              const inst = institutions.find((i) => i.code === row.code);
              return (
                <tr key={row.code} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm text-slate-800">
                    <div className="flex flex-col">
                      <span className="font-medium text-slate-900">{row.code}</span>
                      <span className="text-xs text-slate-500">{inst?.city || row.name}</span>
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-800">{row.budget_alloue_tnd.toLocaleString('fr-FR')}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-800">{row.budget_execute_tnd.toLocaleString('fr-FR')}</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-900">{execution.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-800">{row.payroll_ratio.toFixed(1)}%</td>
                  <td className="px-4 py-3 text-sm text-right font-tabular text-slate-800">{row.external_funding_tnd.toLocaleString('fr-FR')}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </section>
    </div>
  );
}
