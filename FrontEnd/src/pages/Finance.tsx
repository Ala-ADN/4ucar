import { institutions } from '@/src/data/dashboardMock';

export function Finance() {
  const financeRows = institutions.map((item) => {
    const allocated = Math.round(item.students * 1650);
    const executed = Math.round((allocated * item.kpiSnapshot.documentControlCompliance) / 100);
    return {
      code: item.code,
      name: item.name,
      city: item.city,
      budget_alloue_tnd: allocated,
      budget_execute_tnd: executed,
      payroll_ratio: Number((100 - item.kpiSnapshot.workloadCompliance / 2).toFixed(1)),
      external_funding_tnd: Math.round(item.kpiSnapshot.successRate * 4200),
    };
  });

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
        <p className="text-sm text-slate-600 mt-1">Exécution budgétaire et soutenabilité par établissement</p>
      </div>

      <section className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-sm text-slate-600">Budget réseau alloué</p>
          <p className="text-2xl font-semibold text-slate-900 mt-2">{Math.round(totalBudget / 1000000)} M TND</p>
        </div>
        <div className="bg-white border border-slate-200 rounded-md p-4">
          <p className="text-sm text-slate-600">Exécution globale</p>
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
              <th className="px-4 py-3 text-xs font-semibold text-slate-700">Établissement</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Alloué (TND)</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Exécuté (TND)</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Exécution</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Masse salariale</th>
              <th className="px-4 py-3 text-xs font-semibold text-slate-700 text-right">Financement externe</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-200">
            {financeRows.map((row) => {
              const execution = (row.budget_execute_tnd / row.budget_alloue_tnd) * 100;
              return (
                <tr key={row.code} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-sm text-slate-800">
                    <div className="flex flex-col">
                      <span className="font-medium text-slate-900">{row.code}</span>
                      <span className="text-xs text-slate-500">{row.city}</span>
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
