export interface SegmentDepth {
  t0?: number;
  t30?: number;
  t60?: number;
  t90?: number;
  t120?: number;
  t180?: number;
  [key: string]: number | undefined;
}

export interface FloodSegment {
  id: string;
  name: string;
  zone: string;
  road_class: string;
  osm_type?: string;
  elevation: number;
  pipe_dia: number;
  theoretical_cap: number;
  mu_clog: number;
  manning_n: number;
  chronic: number;
  coords: [number, number][];
  depths?: SegmentDepth;
  peak_depth?: number;
}

export interface HotspotManhole {
  id: string;
  name: string;
  location: string;
  lat: number;
  lon: number;
  lng?: number;
  zone: string;
  elevation: number;
  ground_elevation?: number;
  pipe_dia_mm?: number;
  diameter_mm?: number;
  theoretical_cap?: number;
  manning_n?: number;
  clog_mu?: number;
  hgl: number;
  hgl_steps?: SegmentDepth;
  backflow_m3s: number;
  blockage_type: string;
  source: string;
  confidence: string;
  complaint_date?: string;
}

export interface Substation {
  id: string;
  name: string;
  voltage: string;
  voltage_kv: number;
  type: string;
  elevation_m: number;
  plinth_cm: number;
  status: string;
  flood_risk: string;
  criticality: string;
  lat: number;
  lon: number;
  lng?: number;
}

export interface RouteScenario {
  title: string;
  origin: string;
  origin_coords: [number, number];
  destination: string;
  destination_coords: [number, number];
  direct: [number, number][];
  direct_bottleneck_depth_cm: number;
  direct_distance_km: number;
  direct_eta_min: number;
  direct_bottleneck_location: string;
  direct_warning: string;
  direct_status: string;
  safe: [number, number][];
  safe_max_depth_cm: number;
  safe_distance_km: number;
  safe_eta_min: number;
  detour_extra_km: number;
  detour_extra_min: number;
  safe_corridor: string;
  safe_status: string;
  turn_by_turn: string[];
}

export interface MasterFloodData {
  metadata: {
    city: string;
    total_segments_analyzed: number;
    active_demo_segments: number;
    substations_count: number;
    surcharge_hotspots_count: number;
    timestamp: string;
    radar_station: string;
    baseline_hyetograph_mm_hr: { time: string; rain: number }[];
  };
  segments: FloodSegment[];
  hotspots: HotspotManhole[];
  substations: Substation[];
  routes: {
    scenario1: RouteScenario;
    scenario2: RouteScenario;
  };
}

declare global {
  interface Window {
    CHENNAI_FLOOD_DATA?: MasterFloodData;
  }
}

export function getMasterFloodData(): MasterFloodData | null {
  if (typeof window !== 'undefined' && window.CHENNAI_FLOOD_DATA) {
    return window.CHENNAI_FLOOD_DATA;
  }
  return null;
}
