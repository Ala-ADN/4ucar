import { motion } from 'motion/react';
import { LucideIcon, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { cn } from '@/src/lib/utils';
import { useEffect, useState } from 'react';

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
  const [displayValue, setDisplayValue] = useState(0);

  useEffect(() => {
    if (typeof value === 'number') {
      const duration = 1000;
      const start = 0;
      const end = value;
      let startTime: number;

      const animate = (time: number) => {
        if (!startTime) startTime = time;
        const progress = Math.min((time - startTime) / duration, 1);
        setDisplayValue(start + progress * (end - start));
        if (progress < 1) requestAnimationFrame(animate);
      };
      
      requestAnimationFrame(animate);
    }
  }, [value]);

  const formattedValue = typeof value === 'number' 
    ? displayValue.toLocaleString('fr-FR', { 
        maximumFractionDigits: value % 1 === 0 ? 0 : 1 
      }) 
    : value;

  const isTrendUp = trend ? trend.value > 0 : false;
  const isGoodTrend = trend 
    ? (trend.value > 0 && (trend.isPositiveGood ?? true)) || (trend.value < 0 && !(trend.isPositiveGood ?? true))
    : false;

  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm transition-all"
    >
      <div className="flex justify-between items-start mb-4">
        <div className="bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-slate-600">
          <Icon size={18} />
        </div>
        {trend && (
          <span className={cn(
            "text-[11px] font-bold px-2 py-1 rounded-md font-tabular",
            isGoodTrend ? "bg-green-50 text-green-600" : "bg-red-50 text-red-600"
          )}>
            {isTrendUp ? "+" : ""}{trend.value}{trend.unit}
          </span>
        )}
      </div>

      <div className="space-y-1">
        <p className="text-slate-500 text-xs font-semibold uppercase tracking-wider">
          {label}
        </p>
        <div className="flex items-baseline gap-1.5">
          <span className="text-4xl font-bold text-slate-900 tabular-nums">
            {formattedValue}{suffix}
          </span>
          {badge && (
            <span className="bg-slate-900 text-white px-2 py-0.5 rounded-md text-[10px] font-bold uppercase tracking-tight">
              {badge}
            </span>
          )}
        </div>
      </div>
    </motion.div>
  );
}
