import MapWidget from '../widgets/MapWidget';
import CloggingWidget from '../widgets/CloggingWidget';
import TidalWidget from '../widgets/TidalWidget';
import AlertsWidget from '../widgets/AlertsWidget';
import PredictionsWidget from '../widgets/PredictionsWidget';
import { Bell, LayoutGrid, LogOut } from 'lucide-react';

export default function DashboardLayout() {
  return (
    <div className="w-screen h-screen overflow-hidden bg-[#0c101a] font-sans text-slate-300 flex flex-col select-none">
      {/* Top Header Bar */}
      <header className="h-14 px-6 flex items-center justify-between flex-shrink-0 z-20">
        {/* Left: Pulse Waveform Logo + Nowcasting System */}
        <div className="flex items-center gap-3">
          <svg className="w-8 h-8" viewBox="0 0 32 32" fill="none">
            <defs>
              <linearGradient id="waveLogoGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#8b5cf6" />
                <stop offset="50%" stopColor="#00d2ff" />
                <stop offset="100%" stopColor="#06b6d4" />
              </linearGradient>
            </defs>
            <path
              d="M 2 16 L 6 16 L 9 8 L 13 24 L 17 4 L 21 26 L 24 16 L 30 16"
              stroke="url(#waveLogoGrad)"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span className="text-base font-bold text-white tracking-wide">
            Nowcasting System
          </span>
        </div>

        {/* Center: Chennai City & Web dashboard */}
        <div className="text-left -ml-24">
          <h1 className="text-lg font-bold text-white leading-tight">Chennai City</h1>
          <p className="text-[11px] text-slate-400 leading-none">Web dashboard</p>
        </div>

        {/* Right: 3 Nav Icons */}
        <div className="flex items-center gap-4 text-slate-400">
          <button className="hover:text-white transition-colors cursor-pointer">
            <LayoutGrid className="w-4 h-4" />
          </button>
          <button className="relative hover:text-white transition-colors cursor-pointer">
            <Bell className="w-4 h-4" />
            <span className="absolute -top-1.5 -right-1.5 w-3.5 h-3.5 bg-[#ff3b30] text-[9px] font-bold text-white rounded-full flex items-center justify-center">
              1
            </span>
          </button>
          <button className="hover:text-white transition-colors cursor-pointer">
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* Main 3-Column Content Layout */}
      <main className="flex-1 px-5 pb-5 pt-1 flex gap-3.5 overflow-hidden min-h-0">
        {/* Left Column Widgets (~280px) */}
        <div className="w-[280px] flex flex-col gap-3 flex-shrink-0 h-full overflow-hidden">
          {/* 1. Live Update + Flood Risk Card */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 shadow-xl flex flex-col gap-2">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2 text-emerald-400 text-xs font-semibold">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_8px_#34d399]"></span>
                Live Update
              </div>
              {/* Green Switch Toggle */}
              <div className="w-9 h-5 bg-emerald-500/20 rounded-full flex items-center p-0.5 border border-emerald-500/40 cursor-pointer">
                <div className="w-4 h-4 bg-emerald-400 rounded-full translate-x-4 shadow-[0_0_6px_#34d399] transition-transform"></div>
              </div>
            </div>
            <div className="text-sm">
              <span className="text-slate-300 font-medium">Flood Risk: </span>
              <span className="text-[#ff3b30] font-bold">HIGH (Red Alert)</span>
            </div>
          </div>

          {/* 2. Clogging Factor Card */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 flex-1 shadow-xl flex flex-col min-h-0">
            <CloggingWidget />
          </div>

          {/* 3. Tidal Stage Card */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 flex-1 shadow-xl flex flex-col min-h-0">
            <TidalWidget />
          </div>
        </div>

        {/* Center Column: Glow Road Network Map Card */}
        <div className="flex-1 h-full min-w-0 relative">
          <MapWidget />
        </div>

        {/* Right Column Widgets (~310px) */}
        <div className="w-[310px] flex flex-col gap-3 flex-shrink-0 h-full overflow-hidden">
          {/* 1. Surcharge Hotspots List */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 flex-[1.4] shadow-xl flex flex-col min-h-0 overflow-hidden">
            <AlertsWidget />
          </div>

          {/* 2. Total Alerts Counter */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 shadow-xl flex flex-col justify-between">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-slate-300 tracking-wide">
                Total Alerts <span className="text-slate-500 font-normal">(Last 12h)</span>
              </h3>
              <span className="text-slate-400 text-lg leading-none cursor-pointer hover:text-white">
                ...
              </span>
            </div>
            <div className="text-3xl font-extrabold text-white mt-0.5">42</div>
          </div>

          {/* 3. Active Predictions Area Chart */}
          <div className="bg-[#121826]/90 backdrop-blur-md border border-slate-800/80 rounded-2xl p-3.5 flex-1 shadow-xl flex flex-col min-h-0">
            <PredictionsWidget />
          </div>
        </div>
      </main>
    </div>
  );
}
