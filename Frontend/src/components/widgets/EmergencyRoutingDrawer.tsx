import { useState } from 'react';
import type { RouteScenario } from '../../types/floodData';
import { AlertOctagon, CheckCircle2, Navigation, Compass, X } from 'lucide-react';

interface EmergencyRoutingDrawerProps {
  scenarios: {
    scenario1: RouteScenario;
    scenario2: RouteScenario;
  };
  activeScenarioKey: 'scenario1' | 'scenario2';
  onSelectScenario: (key: 'scenario1' | 'scenario2') => void;
  onClose: () => void;
}

export default function EmergencyRoutingDrawer({
  scenarios,
  activeScenarioKey,
  onSelectScenario,
  onClose,
}: EmergencyRoutingDrawerProps) {
  const [showTurnByTurn, setShowTurnByTurn] = useState(false);
  const activeScenario = scenarios[activeScenarioKey];

  return (
    <div className="absolute bottom-16 left-4 z-[1000] w-96 max-w-[calc(100%-2rem)] bg-[#0c1424]/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-4 shadow-2xl animate-in slide-in-from-bottom-4">
      {/* Header */}
      <div className="flex items-center justify-between pb-2 border-b border-slate-800">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-rose-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-200">
            Emergency Evacuation Routing
          </h3>
        </div>
        <button
          onClick={onClose}
          className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Scenario Selector Tabs */}
      <div className="flex gap-1.5 my-2.5">
        <button
          onClick={() => onSelectScenario('scenario1')}
          className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all truncate text-left ${
            activeScenarioKey === 'scenario1'
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              : 'bg-slate-900/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          1. Velachery &rarr; Guindy
        </button>
        <button
          onClick={() => onSelectScenario('scenario2')}
          className={`flex-1 py-1.5 px-2 rounded-lg text-xs font-semibold transition-all truncate text-left ${
            activeScenarioKey === 'scenario2'
              ? 'bg-rose-500/20 text-rose-300 border border-rose-500/40'
              : 'bg-slate-900/60 text-slate-400 hover:text-slate-200'
          }`}
        >
          2. KMC &rarr; Central
        </button>
      </div>

      {/* Scenario Overview */}
      <div className="text-xs text-slate-300 mb-2 font-medium">
        {activeScenario.title}
      </div>

      {/* Direct vs Safe Route Comparison */}
      <div className="space-y-2">
        {/* Direct Bottleneck Route */}
        <div className="p-2.5 rounded-xl bg-red-950/30 border border-red-500/30 flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs font-bold text-red-400">
            <span className="flex items-center gap-1.5">
              <AlertOctagon className="w-3.5 h-3.5 text-red-500" />
              Direct Route (Flooded)
            </span>
            <span>{activeScenario.direct_distance_km} km / {activeScenario.direct_eta_min}m</span>
          </div>
          <div className="text-[11px] text-red-300/90 leading-tight">
            Max Depth: <span className="font-bold text-red-200">{activeScenario.direct_bottleneck_depth_cm} cm</span> (At {activeScenario.direct_bottleneck_location})
          </div>
          <div className="text-[10px] text-red-400 font-semibold bg-red-500/10 px-2 py-0.5 rounded mt-0.5">
            {activeScenario.direct_status}
          </div>
        </div>

        {/* Safe Ridge Route */}
        <div className="p-2.5 rounded-xl bg-emerald-950/30 border border-emerald-500/30 flex flex-col gap-1">
          <div className="flex items-center justify-between text-xs font-bold text-emerald-400">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
              Safe Detour Corridor
            </span>
            <span>{activeScenario.safe_distance_km} km / {activeScenario.safe_eta_min}m</span>
          </div>
          <div className="text-[11px] text-emerald-300/90 leading-tight">
            Max Depth: <span className="font-bold text-emerald-200">{activeScenario.safe_max_depth_cm} cm</span> ({activeScenario.safe_corridor})
          </div>
          <div className="text-[10px] text-emerald-300 font-semibold bg-emerald-500/10 px-2 py-0.5 rounded mt-0.5 flex justify-between">
            <span>{activeScenario.safe_status}</span>
            <span>+{activeScenario.detour_extra_km} km ({activeScenario.detour_extra_min}m)</span>
          </div>
        </div>
      </div>

      {/* Turn-by-Turn Accordion Toggle */}
      <button
        onClick={() => setShowTurnByTurn(!showTurnByTurn)}
        className="w-full mt-2.5 py-1 px-2 rounded-lg bg-slate-800/60 hover:bg-slate-800 text-[11px] font-semibold text-slate-300 flex items-center justify-center gap-1.5 transition-colors"
      >
        <Compass className="w-3.5 h-3.5 text-cyan-400" />
        {showTurnByTurn ? 'Hide Turn-by-Turn Guidance' : 'Show Turn-by-Turn Guidance'}
      </button>

      {showTurnByTurn && (
        <div className="mt-2 max-h-36 overflow-y-auto space-y-1.5 pr-1 border-t border-slate-800/80 pt-2 text-[11px] text-slate-300">
          {activeScenario.turn_by_turn.map((step, idx) => (
            <div key={idx} className="flex gap-2 items-start">
              <span className="w-4 h-4 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center text-[10px] font-bold shrink-0 mt-0.5">
                {idx + 1}
              </span>
              <span className="leading-snug text-slate-300">{step}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
