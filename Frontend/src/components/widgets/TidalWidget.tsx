import { ChevronRight, ArrowUpRight } from 'lucide-react';

export default function TidalWidget() {
  return (
    <div className="flex flex-col h-full w-full justify-between">
      {/* Header */}
      <div className="flex items-center justify-between text-slate-300">
        <h3 className="text-[13px] font-medium tracking-wide">Tidal Stage</h3>
        <ChevronRight className="w-4 h-4 text-slate-400 cursor-pointer hover:text-white transition-colors" />
      </div>

      {/* Main Value */}
      <div className="text-3xl font-extrabold text-white mt-1">2.1m</div>

      {/* Smooth Continuous Spline Wave SVG with glowing peak dot */}
      <div className="relative w-full h-20 my-1 overflow-visible">
        <svg viewBox="0 0 280 80" className="w-full h-full overflow-visible" preserveAspectRatio="none">
          <defs>
            {/* Cyan Gradient Fill */}
            <linearGradient id="tidalGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#00d2ff" stopOpacity={0.4} />
              <stop offset="100%" stopColor="#00d2ff" stopOpacity={0.0} />
            </linearGradient>

            {/* Cyan Glow Filter */}
            <filter id="cyanGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Area Fill under curve */}
          <path
            d="M 0 65 Q 40 75 70 55 T 140 25 T 210 50 T 280 30 L 280 80 L 0 80 Z"
            fill="url(#tidalGradient)"
          />

          {/* Glowing Stroke Curve */}
          <path
            d="M 0 65 Q 40 75 70 55 T 140 25 T 210 50 T 280 30"
            fill="none"
            stroke="#00d2ff"
            strokeWidth="3"
            strokeLinecap="round"
            filter="url(#cyanGlow)"
          />

          {/* Outer soft glow stroke */}
          <path
            d="M 0 65 Q 40 75 70 55 T 140 25 T 210 50 T 280 30"
            fill="none"
            stroke="#00d2ff"
            strokeWidth="6"
            strokeLinecap="round"
            opacity="0.3"
            filter="blur(4px)"
          />

          {/* Glowing White Peak Dot at (140, 25) */}
          <circle cx="140" cy="25" r="7" fill="#00d2ff" opacity="0.3" className="animate-ping" />
          <circle cx="140" cy="25" r="5" fill="#00d2ff" opacity="0.8" />
          <circle cx="140" cy="25" r="3" fill="#ffffff" filter="drop-shadow(0 0 6px #00d2ff)" />
        </svg>
      </div>

      {/* Footer Info */}
      <div className="flex items-center justify-between pt-2 border-t border-slate-800/60 text-xs">
        <span className="text-slate-400">Tidal Prediction</span>
        <span className="text-slate-200 font-medium flex items-center gap-1">
          High Tide in 1h 30m
          <ArrowUpRight className="w-4 h-4 text-purple-400 stroke-[2.5]" />
        </span>
      </div>
    </div>
  );
}
