import { LucideIcon } from 'lucide-react';
import { cn } from '@/src/lib/utils';

interface KPICardProps {
  label: string;
  value: number | string;
  trend?: {
    value: number;
    unit?: string;
    isPositiveGood?: boolean;
  };
  suffix?: string;
  icon: LucideIcon;
  badge?: string;
}

export function KPICard({ label, value, trend, suffix = '', icon: Icon, badge }: KPICardProps) {
  const formattedValue = typeof value === 'number' 
    ? value.toLocaleString('fr-FR', { 
        maximumFractionDigits: value % 1 === 0 ? 0 : 1 
      }) 
    : value;

  const isTrendUp = trend ? trend.value > 0 : false;
  const isGoodTrend = trend 
    ? (trend.value > 0 && (trend.isPositiveGood ?? true)) || (trend.value < 0 && !(trend.isPositiveGood ?? true))
    : false;

  return (
    <div className="bg-white p-5 rounded-md border border-slate-200 shadow-sm flex flex-col justify-between transition-colors duration-150 hover:border-slate-300">
      <div className="flex justify-between items-start mb-4">
        <div className="text-slate-500">
          <Icon size={20} />
        </div>
        {trend && (
          <span className={cn(
            "text-xs font-medium px-2 py-1 rounded font-tabular",
            isGoodTrend ? "bg-green-50 text-green-700" : "bg-red-50 text-red-700"
          )}>
            {isTrendUp ? "+" : ""}{trend.value}{trend.unit}
          </span>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-slate-600 text-sm font-semibold uppercase tracking-wide">
          {label}
        </p>
        <div className="flex items-baseline gap-1.5 mt-2">
          <span className="text-3xl font-bold text-slate-900 tabular-nums">
            {formattedValue}{suffix}
          </span>
          {badge && (
            <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-tight ml-2">
              {badge}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
