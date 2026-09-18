import { AlertTriangle, MapPin } from 'lucide-react';

interface Manhole {
  id: string;
  location: string;
  depth: string;
  risk: 'High Risk' | 'Elevated Risk';
  riskColor: string;
  borderColor: string;
  bgGlow: string;
  pinColor: string;
}

const MANHOLES: Manhole[] = [
  {
    id: 'MH-041',
    location: 'Kodambakkam',
    depth: '1.2m Depth',
    risk: 'High Risk',
    riskColor: 'text-[#ff3b30]',
    borderColor: 'border-red-500/20 hover:border-red-500/50',
    bgGlow: 'bg-red-500/5',
    pinColor: '#ff3b30',
  },
  {
    id: 'MH-118',
    location: 'Anna Nagar',
    depth: '0.9m Depth',
    risk: 'High Risk',
    riskColor: 'text-[#ff9500]',
    borderColor: 'border-orange-500/20 hover:border-orange-500/50',
    bgGlow: 'bg-orange-500/5',
    pinColor: '#ff9500',
  },
  {
    id: 'MH-087',
    location: 'Guindy',
    depth: '1.1m Depth',
    risk: 'High Risk',
    riskColor: 'text-[#ff3b30]',
    borderColor: 'border-red-500/20 hover:border-red-500/50',
    bgGlow: 'bg-red-500/5',
    pinColor: '#ff3b30',
  },
  {
    id: 'MH-162',
    location: 'Velachery',
    depth: '0.7m Depth',
    risk: 'Elevated Risk',
    riskColor: 'text-[#ffcc00]',
    borderColor: 'border-yellow-500/20 hover:border-yellow-500/50',
    bgGlow: 'bg-yellow-500/5',
    pinColor: '#ffcc00',
  },
];

export default function AlertsWidget() {
  return (
    <div className="flex flex-col h-full w-full justify-between">
      {/* Header */}
      <div className="flex items-center justify-between mb-2 flex-shrink-0">
        <h3 className="text-[13px] font-semibold text-slate-200 tracking-wide">
          Surcharge Hotspot Manholes
        </h3>
        <span className="text-slate-400 text-lg leading-none cursor-pointer hover:text-white">
          ...
        </span>
      </div>

      {/* List of 4 Manholes */}
      <div className="flex flex-col gap-2 overflow-y-auto pr-1">
        {MANHOLES.map((mh) => (
          <div
            key={mh.id}
            className={`flex items-center justify-between p-2 rounded-xl bg-[#141b2a]/90 border ${mh.borderColor} ${mh.bgGlow} transition-all duration-200 hover:scale-[1.01]`}
          >
            {/* Left: Mini Map Thumbnail with Glowing Pin */}
            <div className="w-12 h-12 rounded-lg bg-[#0a0f1d] border border-slate-700/60 flex items-center justify-center relative overflow-hidden flex-shrink-0">
              {/* Stylized mini road grid in background */}
              <svg className="absolute inset-0 w-full h-full opacity-30" viewBox="0 0 48 48">
                <path d="M 0 16 L 48 16 M 0 32 L 48 32 M 16 0 L 16 48 M 32 0 L 32 48" stroke="#38bdf8" strokeWidth="1" />
                <path d="M 6 42 L 42 6" stroke="#ff3b30" strokeWidth="1.5" opacity="0.6" />
              </svg>
              {/* Glowing Pin */}
              <MapPin className="w-5 h-5 relative z-10 drop-shadow-[0_0_6px_currentColor]" style={{ color: mh.pinColor }} />
            </div>

            {/* Center: Info */}
            <div className="flex-1 min-w-0 mx-3 flex flex-col justify-center">
              <div className="text-xs font-semibold text-white truncate">
                {mh.id} ({mh.location})
              </div>
              <div className="text-[11px] text-slate-400 mt-0.5">{mh.depth}</div>
              <div className={`text-[11px] font-medium mt-0.5 ${mh.riskColor}`}>{mh.risk}</div>
            </div>

            {/* Right: Alert Warning Icon */}
            <div className="pr-1 flex items-center justify-center flex-shrink-0">
              <AlertTriangle className="w-4 h-4 drop-shadow-[0_0_6px_currentColor]" style={{ color: mh.pinColor }} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
