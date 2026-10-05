import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: LucideIcon;
  sublabel?: string;
  color?: 'indigo' | 'emerald' | 'amber' | 'blue' | 'rose' | 'slate';
  onClick?: () => void;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon: Icon,
  sublabel,
  color = 'indigo',
  onClick
}) => {
  const colorMap = {
    indigo: {
      bg: 'bg-indigo-500/10',
      border: 'border-indigo-500/20',
      text: 'text-indigo-400',
      hover: 'hover:border-indigo-500/40'
    },
    emerald: {
      bg: 'bg-emerald-500/10',
      border: 'border-emerald-500/20',
      text: 'text-emerald-400',
      hover: 'hover:border-emerald-500/40'
    },
    amber: {
      bg: 'bg-amber-500/10',
      border: 'border-amber-500/20',
      text: 'text-amber-400',
      hover: 'hover:border-amber-500/40'
    },
    blue: {
      bg: 'bg-blue-500/10',
      border: 'border-blue-500/20',
      text: 'text-blue-400',
      hover: 'hover:border-blue-500/40'
    },
    rose: {
      bg: 'bg-rose-500/10',
      border: 'border-rose-500/20',
      text: 'text-rose-400',
      hover: 'hover:border-rose-500/40'
    },
    slate: {
      bg: 'bg-slate-800/40',
      border: 'border-slate-800',
      text: 'text-slate-400',
      hover: 'hover:border-slate-700'
    }
  };

  const scheme = colorMap[color];

  return (
    <div
      onClick={onClick}
      className={`p-5 rounded-xl bg-slate-900/80 border ${scheme.border} transition-all ${
        onClick ? `cursor-pointer ${scheme.hover} active:scale-[0.99]` : ''
      }`}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</p>
          <p className="text-2xl font-bold text-white mt-1.5">{value}</p>
          {sublabel && <p className="text-xs text-slate-400 mt-1">{sublabel}</p>}
        </div>
        <div className={`w-12 h-12 rounded-xl ${scheme.bg} flex items-center justify-center border ${scheme.border}`}>
          <Icon className={`w-6 h-6 ${scheme.text}`} />
        </div>
      </div>
    </div>
  );
};
