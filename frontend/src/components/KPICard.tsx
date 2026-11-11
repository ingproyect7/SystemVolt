import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  unit?: string;
  icon: LucideIcon;
  subtext?: string;
  status?: 'normal' | 'warning' | 'critical';
  trend?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  icon: Icon,
  subtext,
  status = 'normal',
  trend
}) => {
  const statusStyles = {
    normal: 'border-slate-800 bg-slate-900/80 text-white',
    warning: 'border-amber-500/30 bg-amber-950/20 text-amber-200',
    critical: 'border-red-500/40 bg-red-950/25 text-red-200',
  };

  const iconColors = {
    normal: 'text-amber-500 bg-amber-500/10',
    warning: 'text-amber-400 bg-amber-500/20',
    critical: 'text-red-400 bg-red-500/20',
  };

  return (
    <div className={`p-5 rounded-xl border backdrop-blur-sm transition-all hover:border-slate-700 shadow-lg ${statusStyles[status]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-slate-400">{title}</span>
        <div className={`p-2 rounded-lg ${iconColors[status]}`}>
          <Icon className="h-5 w-5" />
        </div>
      </div>
      <div className="mt-4 flex items-baseline space-x-2">
        <span className="text-3xl font-bold font-mono tracking-tight">{value}</span>
        {unit && <span className="text-sm font-medium text-slate-400">{unit}</span>}
      </div>
      {(subtext || trend) && (
        <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
          <span>{subtext}</span>
          {trend && <span className="font-mono text-emerald-400">{trend}</span>}
        </div>
      )}
    </div>
  );
};
