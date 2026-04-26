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
  /** Array of 4-8 numeric values for a tiny inline sparkline */
  sparkline?: number[];
}

/* ─── Minimal Sparkline (no axes, no labels) ─── */

function Sparkline({ data, color = '#1B4F8B' }: { data: number[]; color?: string }) {
  const w = 120;
  const h = 28;
  const pad = 2;

  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;

  const points = data.map((v, i) => {
    const x = pad + (i / (data.length - 1)) * (w - pad * 2);
    const y = h - pad - ((v - min) / range) * (h - pad * 2);
    return `${x},${y}`;
  });

  const polyline = points.join(' ');

  // Create gradient area fill
  const first = points[0];
  const last = points[points.length - 1];
  const areaPath = `M ${first} ${points.slice(1).map(p => `L ${p}`).join(' ')} L ${last.split(',')[0]},${h} L ${first.split(',')[0]},${h} Z`;

  return (
    <svg width={w} height={h} className="shrink-0" viewBox={`0 0 ${w} ${h}`}>
      <defs>
        <linearGradient id={`spark-grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.15" />
          <stop offset="100%" stopColor={color} stopOpacity="0.02" />
        </linearGradient>
      </defs>
      <path d={areaPath} fill={`url(#spark-grad-${color.replace('#', '')})`} />
      <polyline
        points={polyline}
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* End dot */}
      <circle
        cx={parseFloat(points[points.length - 1].split(',')[0])}
        cy={parseFloat(points[points.length - 1].split(',')[1])}
        r="2"
        fill={color}
      />
    </svg>
  );
}

export function KPICard({ label, value, trend, suffix = '', icon: Icon, badge, sparkline }: KPICardProps) {
  const formattedValue = typeof value === 'number' 
    ? value.toLocaleString('fr-FR', { 
        maximumFractionDigits: value % 1 === 0 ? 0 : 1 
      }) 
    : value;

  const isTrendUp = trend ? trend.value > 0 : false;
  const isGoodTrend = trend 
    ? (trend.value > 0 && (trend.isPositiveGood ?? true)) || (trend.value < 0 && !(trend.isPositiveGood ?? true))
    : false;

  // Choose sparkline color based on trend
  const sparkColor = trend
    ? isGoodTrend ? '#16A34A' : '#EF4444'
    : '#1B4F8B';

  return (
    <div className="bg-white p-6 rounded-lg border border-slate-200 flex flex-col justify-between transition-colors duration-150 hover:border-slate-300">
      <div className="flex justify-between items-start mb-4">
        <div className="text-slate-400">
          <Icon size={20} strokeWidth={1.6} />
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
        <p className="text-slate-500 text-xs font-semibold uppercase tracking-wide">
          {label}
        </p>
        <div className="flex items-baseline gap-1.5 mt-1.5">
          <span className="text-3xl font-bold text-slate-900 tabular-nums tracking-tight">
            {formattedValue}{suffix}
          </span>
          {badge && (
            <span className="bg-slate-100 text-slate-700 px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-tight ml-2">
              {badge}
            </span>
          )}
        </div>
      </div>

      {/* Sparkline */}
      {sparkline && sparkline.length >= 3 && (
        <div className="mt-3 pt-3 border-t border-slate-100">
          <Sparkline data={sparkline} color={sparkColor} />
        </div>
      )}
    </div>
  );
}
