import { Layers, Mountain, Waves, Zap, Ambulance } from 'lucide-react';

export const TwinLayerMode = {
  inundation: 'inundation',
  hydraulics: 'hydraulics',
  dem: 'dem',
  routing: 'routing',
} as const;
export type TwinLayerMode = 'inundation' | 'hydraulics' | 'dem' | 'routing';

export interface LayerVisibility {
  roads: boolean;
  manholes: boolean;
  substations: boolean;
  dem: boolean;
  routing: boolean;
}

interface TwinLayerControlProps {
  activeMode: TwinLayerMode;
  onModeChange: (mode: TwinLayerMode) => void;
  visibility: LayerVisibility;
  onVisibilityChange: (vis: LayerVisibility) => void;
  isOpen: boolean;
  onToggleOpen: () => void;
}

export default function TwinLayerControl({
  activeMode,
  onModeChange,
  visibility,
  onVisibilityChange,
  isOpen,
  onToggleOpen,
}: TwinLayerControlProps) {
  const toggleLayer = (key: keyof LayerVisibility) => {
    onVisibilityChange({
      ...visibility,
      [key]: !visibility[key],
    });
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <button
        onClick={onToggleOpen}
        title="Digital Twin Layers & Filters"
        className={`p-2 rounded-lg border backdrop-blur-md transition-all shadow-lg flex items-center gap-1.5 text-xs font-semibold ${
          isOpen
            ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-300'
            : 'bg-slate-900/80 border-slate-700/60 text-slate-300 hover:text-white hover:bg-slate-800'
        }`}
      >
        <Layers className="w-4 h-4" />
        <span className="hidden sm:inline">Twin Layers</span>
      </button>

      {/* Glass Popover Menu */}
      {isOpen && (
        <div className="absolute right-0 top-11 w-72 bg-[#0d1424]/95 backdrop-blur-xl border border-slate-700/80 rounded-2xl p-3 shadow-2xl z-50 animate-in fade-in zoom-in-95">
          {/* Header */}
          <div className="flex items-center justify-between pb-2 border-b border-slate-800/80">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-200">
              KAIROS Digital Twin Modes
            </span>
            <span className="text-[10px] text-cyan-400 font-mono">v2.4-GCC</span>
          </div>

          {/* 4 Twin Layer Modes */}
          <div className="grid grid-cols-2 gap-1.5 my-2.5">
            <button
              onClick={() => onModeChange('inundation')}
              className={`flex items-center gap-2 p-2 rounded-xl border text-left text-xs font-semibold transition-all ${
                activeMode === 'inundation'
                  ? 'bg-cyan-500/20 border-cyan-400 text-cyan-200 shadow-[0_0_12px_rgba(34,211,238,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Waves className="w-4 h-4 text-cyan-400" />
              <div className="flex flex-col">
                <span className="leading-tight">L3 Inundation</span>
                <span className="text-[9px] text-slate-400 font-normal">PI-GNN Flow</span>
              </div>
            </button>

            <button
              onClick={() => onModeChange('hydraulics')}
              className={`flex items-center gap-2 p-2 rounded-xl border text-left text-xs font-semibold transition-all ${
                activeMode === 'hydraulics'
                  ? 'bg-blue-500/20 border-blue-400 text-blue-200 shadow-[0_0_12px_rgba(59,130,246,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Zap className="w-4 h-4 text-blue-400" />
              <div className="flex flex-col">
                <span className="leading-tight">L2 Hydraulics</span>
                <span className="text-[9px] text-slate-400 font-normal">Pipe Surcharge</span>
              </div>
            </button>

            <button
              onClick={() => onModeChange('dem')}
              className={`flex items-center gap-2 p-2 rounded-xl border text-left text-xs font-semibold transition-all ${
                activeMode === 'dem'
                  ? 'bg-emerald-500/20 border-emerald-400 text-emerald-200 shadow-[0_0_12px_rgba(16,185,129,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Mountain className="w-4 h-4 text-emerald-400" />
              <div className="flex flex-col">
                <span className="leading-tight">L1 Terrain</span>
                <span className="text-[9px] text-slate-400 font-normal">DEM Elevation</span>
              </div>
            </button>

            <button
              onClick={() => onModeChange('routing')}
              className={`flex items-center gap-2 p-2 rounded-xl border text-left text-xs font-semibold transition-all ${
                activeMode === 'routing'
                  ? 'bg-rose-500/20 border-rose-400 text-rose-200 shadow-[0_0_12px_rgba(244,63,94,0.25)]'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
              }`}
            >
              <Ambulance className="w-4 h-4 text-rose-400" />
              <div className="flex flex-col">
                <span className="leading-tight">L4 Routing</span>
                <span className="text-[9px] text-slate-400 font-normal">Safe Corridor</span>
              </div>
            </button>
          </div>

          {/* Interactive Feature Toggles */}
          <div className="pt-2 border-t border-slate-800/80 space-y-1.5">
            <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 px-1 mb-1">
              Display Overlays
            </div>

            <label className="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-slate-800/50 cursor-pointer text-xs text-slate-300">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-cyan-400 shadow-[0_0_6px_#22d3ee]"></span>
                Road Inundation Network
              </span>
              <input
                type="checkbox"
                checked={visibility.roads}
                onChange={() => toggleLayer('roads')}
                className="rounded border-slate-700 bg-slate-800 text-cyan-500 focus:ring-0 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-slate-800/50 cursor-pointer text-xs text-slate-300">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_6px_#ef4444]"></span>
                Surcharge Geyser Manholes
              </span>
              <input
                type="checkbox"
                checked={visibility.manholes}
                onChange={() => toggleLayer('manholes')}
                className="rounded border-slate-700 bg-slate-800 text-red-500 focus:ring-0 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-slate-800/50 cursor-pointer text-xs text-slate-300">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-400 shadow-[0_0_6px_#f59e0b]"></span>
                TNEB Grid Substations
              </span>
              <input
                type="checkbox"
                checked={visibility.substations}
                onChange={() => toggleLayer('substations')}
                className="rounded border-slate-700 bg-slate-800 text-amber-500 focus:ring-0 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-slate-800/50 cursor-pointer text-xs text-slate-300">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-[0_0_6px_#10b981]"></span>
                DEM Elevation Overlay
              </span>
              <input
                type="checkbox"
                checked={visibility.dem}
                onChange={() => toggleLayer('dem')}
                className="rounded border-slate-700 bg-slate-800 text-emerald-500 focus:ring-0 cursor-pointer"
              />
            </label>

            <label className="flex items-center justify-between px-2 py-1 rounded-lg hover:bg-slate-800/50 cursor-pointer text-xs text-slate-300">
              <span className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-rose-400 shadow-[0_0_6px_#f43f5e]"></span>
                Safe Evacuation Routes
              </span>
              <input
                type="checkbox"
                checked={visibility.routing}
                onChange={() => toggleLayer('routing')}
                className="rounded border-slate-700 bg-slate-800 text-rose-500 focus:ring-0 cursor-pointer"
              />
            </label>
          </div>
        </div>
      )}
    </div>
  );
}
