import { X, AlertTriangle } from 'lucide-react';

export interface InspectionData {
  type: 'road' | 'manhole' | 'substation';
  title: string;
  subtitle?: string;
  badge: {
    text: string;
    color: string;
    bg: string;
    border: string;
  };
  metrics: {
    label: string;
    value: string;
    highlight?: boolean;
  }[];
  warning?: string;
  source?: string;
}

interface InspectionDetailModalProps {
  data: InspectionData;
  onClose: () => void;
}

export default function InspectionDetailModal({ data, onClose }: InspectionDetailModalProps) {
  return (
    <div className="absolute top-4 left-4 z-[1000] w-80 bg-[#0d1527]/95 backdrop-blur-xl border border-cyan-500/40 rounded-2xl p-4 shadow-2xl animate-in fade-in slide-in-from-top-3">
      {/* Header */}
      <div className="flex items-start justify-between gap-2">
        <div>
          <div className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-cyan-400">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse"></span>
            {data.type === 'manhole'
              ? 'Hydraulic Surcharge Geyser'
              : data.type === 'substation'
              ? 'Grid Substation Telemetry'
              : 'Road Inundation Asset'}
          </div>
          <h3 className="text-sm font-bold text-white mt-0.5 leading-snug">{data.title}</h3>
          {data.subtitle && <p className="text-[11px] text-slate-400">{data.subtitle}</p>}
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Risk Badge */}
      <div className="mt-2.5 flex items-center gap-2">
        <span
          className={`px-2.5 py-0.5 rounded-md text-[11px] font-bold uppercase tracking-wider border ${data.badge.bg} ${data.badge.color} ${data.badge.border}`}
        >
          {data.badge.text}
        </span>
      </div>

      {/* Warning Box */}
      {data.warning && (
        <div className="mt-2.5 p-2 rounded-xl bg-red-950/40 border border-red-500/40 text-[11px] text-red-300 flex items-start gap-2">
          <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
          <span className="leading-snug">{data.warning}</span>
        </div>
      )}

      {/* Metrics Grid */}
      <div className="mt-3 grid grid-cols-2 gap-2 border-t border-slate-800/80 pt-2.5">
        {data.metrics.map((m, idx) => (
          <div key={idx} className="bg-slate-900/60 p-2 rounded-lg border border-slate-800">
            <div className="text-[10px] text-slate-400 uppercase font-medium">{m.label}</div>
            <div
              className={`text-xs font-bold mt-0.5 ${
                m.highlight ? 'text-cyan-400' : 'text-slate-200'
              }`}
            >
              {m.value}
            </div>
          </div>
        ))}
      </div>

      {/* Source citation */}
      {data.source && (
        <div className="mt-2.5 text-[10px] text-slate-500 flex items-center justify-between border-t border-slate-800/60 pt-1.5">
          <span>Source:</span>
          <span className="text-slate-400 font-medium truncate max-w-[180px]">{data.source}</span>
        </div>
      )}
    </div>
  );
}
