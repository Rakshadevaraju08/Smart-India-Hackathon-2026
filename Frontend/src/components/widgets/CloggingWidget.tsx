import { ChevronRight } from 'lucide-react';

export default function CloggingWidget() {
  const value = 78;

  // Semicircular SVG Gauge calculation
  // Radius = 75, Center = (100, 95)
  // Total arc length for semicircle = PI * R = 3.14159 * 75 ~= 235.6
  const radius = 75;
  const strokeWidth = 14;
  const circumference = Math.PI * radius;
  const progressOffset = circumference - (value / 100) * circumference;

  return (
    <div className="flex flex-col h-full w-full justify-between">
      {/* Header */}
      <div className="flex items-center justify-between text-slate-300">
        <h3 className="text-[13px] font-medium tracking-wide">Current Clogging Factor</h3>
        <ChevronRight className="w-4 h-4 text-slate-400 cursor-pointer hover:text-white transition-colors" />
      </div>

      {/* Semicircular Gauge */}
      <div className="relative w-full flex flex-col items-center justify-center my-1">
        <svg viewBox="0 0 200 115" className="w-48 overflow-visible">
          <defs>
            {/* Red Neon Gradient */}
            <linearGradient id="gaugeGradient" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#ff3366" />
              <stop offset="50%" stopColor="#ff1a40" />
              <stop offset="100%" stopColor="#ff5252" />
            </linearGradient>

            {/* Neon Glow Filter */}
            <filter id="redGlow" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="4" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Background Track Arc */}
          <path
            d="M 25 95 A 75 75 0 0 1 175 95"
            fill="none"
            stroke="#1e293b"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
          />

          {/* Active Red Glowing Arc */}
          <path
            d="M 25 95 A 75 75 0 0 1 175 95"
            fill="none"
            stroke="url(#gaugeGradient)"
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={progressOffset}
            strokeLinecap="round"
            filter="url(#redGlow)"
          />

          {/* Subtle Outer Bloom */}
          <path
            d="M 25 95 A 75 75 0 0 1 175 95"
            fill="none"
            stroke="#ff1a40"
            strokeWidth={strokeWidth + 6}
            strokeDasharray={circumference}
            strokeDashoffset={progressOffset}
            strokeLinecap="round"
            opacity="0.25"
            filter="blur(5px)"
          />
        </svg>

        {/* Center Text */}
        <div className="absolute top-10 flex flex-col items-center justify-center">
          <div className="text-3xl font-extrabold text-white tracking-tight leading-none">
            {value}%
          </div>
          <div className="text-[11px] font-semibold text-[#ff3366] mt-1 tracking-wider">
            Critical
          </div>
        </div>

        {/* Bottom Ticks: 0 and 78% */}
        <div className="w-48 flex justify-between px-2 -mt-2 text-[10px] text-slate-500 font-medium">
          <span>0</span>
          <span>78%</span>
        </div>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
        <span className="text-slate-400">Sewer System Efficiency</span>
        <span className="text-base font-bold text-white">22%</span>
      </div>
    </div>
  );
}
