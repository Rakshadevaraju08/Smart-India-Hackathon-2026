import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { Play, Pause, Maximize2, Minimize2, Plus, Minus, RotateCcw } from 'lucide-react';
import { getMasterFloodData } from '../../types/floodData';
import type { FloodSegment, HotspotManhole, Substation } from '../../types/floodData';
import TwinLayerControl, { TwinLayerMode } from './TwinLayerControl';
import type { LayerVisibility } from './TwinLayerControl';
import EmergencyRoutingDrawer from './EmergencyRoutingDrawer';
import InspectionDetailModal from './InspectionDetailModal';
import type { InspectionData } from './InspectionDetailModal';

// Clean Primary Arterial Corridors matching screenshot layout
interface BaselineRoad {
  id: string;
  name: string;
  category: string;
  risk: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'NORMAL';
  surcharge: number;
  depth: string;
  flow: string;
  coords: [number, number][];
}

const CHENNAI_CENTER: [number, number] = [13.0450, 80.2480];
const DEFAULT_ZOOM = 12;

const BASELINE_ARTERIALS: BaselineRoad[] = [
  // 1. Kamarajar Salai (Marina Beach Corridor) - Surcharge coastal highway
  {
    id: 'road-marina',
    name: 'Kamarajar Salai (Marina Beach)',
    category: 'Coastal Highway',
    risk: 'CRITICAL',
    surcharge: 94,
    depth: '1.25m',
    flow: '6.4 m³/s',
    coords: [
      [13.0280, 80.2790],
      [13.0335, 80.2800],
      [13.0400, 80.2805],
      [13.0470, 80.2825],
      [13.0530, 80.2835],
      [13.0640, 80.2850],
      [13.0695, 80.2865],
      [13.0780, 80.2920],
      [13.0880, 80.2970],
    ]
  },
  // 2. Chennai Port Loop & Ennore Gateway
  {
    id: 'road-port-loop',
    name: 'Chennai Port Surcharge Corridor',
    category: 'Harbour Access',
    risk: 'CRITICAL',
    surcharge: 91,
    depth: '1.18m',
    flow: '5.8 m³/s',
    coords: [
      [13.0880, 80.2970],
      [13.0950, 80.2995],
      [13.1020, 80.3010],
      [13.1050, 80.2970],
      [13.0970, 80.2920],
      [13.0880, 80.2930],
      [13.0880, 80.2970]
    ]
  },
  // 3. Anna Salai (Mount Road) - Central diagonal spine
  {
    id: 'road-anna-salai',
    name: 'Anna Salai (Mount Road)',
    category: 'Primary Arterial',
    risk: 'CRITICAL',
    surcharge: 89,
    depth: '1.10m',
    flow: '5.5 m³/s',
    coords: [
      [13.0815, 80.2760],
      [13.0730, 80.2710],
      [13.0640, 80.2630],
      [13.0540, 80.2520],
      [13.0450, 80.2450],
      [13.0330, 80.2370],
      [13.0210, 80.2260],
      [13.0120, 80.2130],
      [13.0070, 80.2030],
    ]
  },
  // 4. Sardar Patel Road & Adyar Corridor
  {
    id: 'road-adyar',
    name: 'Sardar Patel Road & Adyar Link',
    category: 'Major Corridor',
    risk: 'CRITICAL',
    surcharge: 87,
    depth: '1.05m',
    flow: '4.9 m³/s',
    coords: [
      [13.0070, 80.2030],
      [13.0110, 80.2180],
      [13.0080, 80.2330],
      [13.0070, 80.2480],
      [13.0060, 80.2580],
      [13.0010, 80.2620],
      [13.0030, 80.2690],
    ]
  },
  // 5. Velachery 100ft Bypass Corridor
  {
    id: 'road-velachery',
    name: 'Velachery 100ft Bypass Corridor',
    category: 'Flood Prone Arterial',
    risk: 'CRITICAL',
    surcharge: 93,
    depth: '1.20m',
    flow: '6.1 m³/s',
    coords: [
      [13.0120, 80.2130],
      [13.0020, 80.2140],
      [12.9910, 80.2155],
      [12.9815, 80.2180],
      [12.9720, 80.2220],
      [12.9640, 80.2260],
    ]
  },
  // 6. Inner Ring Road (100 Feet Road / Jawaharlal Nehru Salai) - Electric Blue Spine
  {
    id: 'road-inner-ring',
    name: 'Inner Ring Road (100 Feet Road)',
    category: 'Express Corridor',
    risk: 'NORMAL',
    surcharge: 38,
    depth: '0.18m',
    flow: '1.6 m³/s',
    coords: [
      [13.0700, 80.1940],
      [13.0590, 80.2020],
      [13.0510, 80.2090],
      [13.0360, 80.2130],
      [13.0230, 80.2090],
      [13.0070, 80.2030]
    ]
  },
  // 7. Poonamallee High Road (EVR Periyar Salai)
  {
    id: 'road-ph-road',
    name: 'Poonamallee High Road (EVR Periyar Salai)',
    category: 'East-West Arterial',
    risk: 'NORMAL',
    surcharge: 42,
    depth: '0.22m',
    flow: '1.9 m³/s',
    coords: [
      [13.0815, 80.2760],
      [13.0820, 80.2650],
      [13.0800, 80.2460],
      [13.0760, 80.2240],
      [13.0730, 80.2080],
      [13.0700, 80.1940]
    ]
  },
  // 8. Dr. Radhakrishnan Salai (Marina to Gemini)
  {
    id: 'road-rk-salai',
    name: 'Dr. Radhakrishnan Salai',
    category: 'Cross Arterial',
    risk: 'HIGH',
    surcharge: 74,
    depth: '0.65m',
    flow: '3.1 m³/s',
    coords: [
      [13.0470, 80.2825],
      [13.0450, 80.2690],
      [13.0460, 80.2580],
      [13.0540, 80.2520]
    ]
  },
  // 9. T. Nagar Commercial Grid (GN Chetty Rd, Usman Rd)
  {
    id: 'road-tnagar-grid',
    name: 'T. Nagar Commercial Arteries',
    category: 'Urban Network',
    risk: 'HIGH',
    surcharge: 81,
    depth: '0.72m',
    flow: '3.8 m³/s',
    coords: [
      [13.0540, 80.2520],
      [13.0440, 80.2410],
      [13.0390, 80.2335],
      [13.0320, 80.2310],
      [13.0210, 80.2260]
    ]
  },
  // 10. Taramani / OMR Link to Adyar
  {
    id: 'road-omr-link',
    name: 'Taramani OMR Connector',
    category: 'IT Corridor Link',
    risk: 'MODERATE',
    surcharge: 62,
    depth: '0.45m',
    flow: '2.8 m³/s',
    coords: [
      [12.9815, 80.2180],
      [12.9800, 80.2360],
      [12.9820, 80.2480],
      [12.9960, 80.2540],
      [13.0060, 80.2580]
    ]
  },
  // 11. Arcot Road (Vadapalani - Kodambakkam - T. Nagar)
  {
    id: 'road-arcot',
    name: 'Arcot Road Link',
    category: 'Urban Connector',
    risk: 'MODERATE',
    surcharge: 68,
    depth: '0.52m',
    flow: '2.5 m³/s',
    coords: [
      [13.0510, 80.2090],
      [13.0480, 80.2230],
      [13.0390, 80.2335]
    ]
  },
  // 12. Greenways & Santhome High Road Link
  {
    id: 'road-greenways',
    name: 'Greenways & Santhome High Road',
    category: 'Coastal Link',
    risk: 'HIGH',
    surcharge: 76,
    depth: '0.70m',
    flow: '3.4 m³/s',
    coords: [
      [13.0060, 80.2580],
      [13.0180, 80.2670],
      [13.0280, 80.2790]
    ]
  }
];

const AREA_LABELS = [
  { id: 'lbl-marina', name: 'MARINA BEACH', pos: [13.0580, 80.2880] as [number, number] },
  { id: 'lbl-port', name: 'CHENNAI PORT', pos: [13.0940, 80.3010] as [number, number] },
  { id: 'lbl-tnagar', name: 'T. NAGAR', pos: [13.0390, 80.2335] as [number, number] },
  { id: 'lbl-adyar', name: 'ADYAR', pos: [13.0070, 80.2580] as [number, number] },
  { id: 'lbl-velachery', name: 'VELACHERY', pos: [12.9770, 80.2180] as [number, number] }
];

// Key Topographical Elevation Diagnostic Hotspots from dem_viewer.html
const DEM_KEY_POINTS = [
  { name: "Marina Beach Road (Kamarajar Salai)", lat: 13.0500, lon: 80.2800, elev: 5.2, slope: "0.008 m/m (0.8%)", aspect: "95° (East to Bay of Bengal)", acc: "High (Coastal Collector)", risk: "CRITICAL (Low Sea Elevation)" },
  { name: "Velachery Main Road / Lake Basin", lat: 12.9815, lon: 80.2180, elev: 6.8, slope: "0.005 m/m (0.5%)", aspect: "110° (East)", acc: "Extremely High (Catchment Sump)", risk: "CRITICAL (Depression Surcharge)" },
  { name: "Gengu Reddy Subway Underpass", lat: 13.0785, lon: 80.2520, elev: 4.8, slope: "0.015 m/m (1.5%)", aspect: "85° (East)", acc: "High (Sag Inflow)", risk: "CRITICAL (Underpass Breach)" },
  { name: "Pulianthope High Road", lat: 13.0950, lon: 80.2650, elev: 6.1, slope: "0.006 m/m (0.6%)", aspect: "90° (East)", acc: "High (Otteri Nullah Catchment)", risk: "HIGH (Canal Backwater)" },
  { name: "T. Nagar (Usman Road)", lat: 13.0418, lon: 80.2341, elev: 14.5, slope: "0.012 m/m (1.2%)", aspect: "98° (East)", acc: "Moderate", risk: "HIGH (Commercial Inundation)" },
  { name: "Nungambakkam High Road (IMD AWS)", lat: 13.0674, lon: 80.2443, elev: 16.0, slope: "0.018 m/m (1.8%)", aspect: "102° (East)", acc: "Moderate", risk: "MODERATE" },
  { name: "Anna University Corridor (Guindy)", lat: 13.0110, lon: 80.2355, elev: 18.2, slope: "0.022 m/m (2.2%)", aspect: "115° (SE)", acc: "Moderate (Adyar Inflow)", risk: "MODERATE" },
  { name: "Kathipara Junction (Alandur)", lat: 13.0067, lon: 80.2026, elev: 21.5, slope: "0.028 m/m (2.8%)", aspect: "120° (SE)", acc: "Low (Elevated Grade)", risk: "LOW" },
];

// Color configs for multi-tier vector bloom (Clean vector strokes, zero buggy CSS blur)
const GLOW_CONFIG = {
  CRITICAL: {
    outer: '#ff1a40',
    mid: '#ff4500',
    core: '#fff3b0',
  },
  HIGH: {
    outer: '#ff7700',
    mid: '#ffaa00',
    core: '#ffffff',
  },
  MODERATE: {
    outer: '#ffcc00',
    mid: '#00e5ff',
    core: '#ffffff',
  },
  NORMAL: {
    outer: '#0066ff',
    mid: '#00d2ff',
    core: '#e0f8ff',
  }
};

const TIMELINE_STEPS = [
  { key: 't0', label: '18:00', sub: 'Live', factor: 1.0 },
  { key: 't30', label: '18:30', sub: '+30m', factor: 1.12 },
  { key: 't60', label: '19:00', sub: '+60m', factor: 1.25 },
  { key: 't90', label: '19:30', sub: '+90m', factor: 1.18 },
  { key: 't120', label: '20:00', sub: '+120m', factor: 1.05 },
  { key: 't180', label: '21:00', sub: '+180m', factor: 0.85 },
];

export default function MapWidget() {
  const mapContainerRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  // Dedicated Layer Groups
  const roadsLayerRef = useRef<L.LayerGroup | null>(null);
  const secondaryRoadsLayerRef = useRef<L.LayerGroup | null>(null);
  const labelsLayerRef = useRef<L.LayerGroup | null>(null);
  const manholesLayerRef = useRef<L.LayerGroup | null>(null);
  const substationsLayerRef = useRef<L.LayerGroup | null>(null);
  const routesLayerRef = useRef<L.LayerGroup | null>(null);
  const demOverlayRef = useRef<L.ImageOverlay | null>(null);

  // States
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [timelineIndex, setTimelineIndex] = useState(0);

  // Twin Layer Controls
  const [twinMode, setTwinMode] = useState<TwinLayerMode>('inundation');
  const [isLayerMenuOpen, setIsLayerMenuOpen] = useState(false);
  const [layerVisibility, setLayerVisibility] = useState<LayerVisibility>({
    roads: true,
    manholes: true,
    substations: true,
    dem: false,
    routing: false,
  });

  // Emergency Routing Drawer
  const [activeRoutingScenario, setActiveRoutingScenario] = useState<'scenario1' | 'scenario2'>('scenario1');
  const [isRoutingDrawerOpen, setIsRoutingDrawerOpen] = useState(false);

  // Inspection Modal
  const [inspectionData, setInspectionData] = useState<InspectionData | null>(null);

  // Auto-play timeline simulation
  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;
    if (isPlaying) {
      interval = setInterval(() => {
        setTimelineIndex((prev) => (prev + 1) % TIMELINE_STEPS.length);
      }, 2400);
    }
    return () => clearInterval(interval);
  }, [isPlaying]);

  // Handle Twin Mode Selection
  const handleModeChange = (mode: TwinLayerMode) => {
    setTwinMode(mode);
    setIsLayerMenuOpen(false);

    if (mode === 'inundation') {
      setLayerVisibility({ roads: true, manholes: false, substations: false, dem: false, routing: false });
      setIsRoutingDrawerOpen(false);
    } else if (mode === 'hydraulics') {
      setLayerVisibility({ roads: true, manholes: true, substations: false, dem: false, routing: false });
      setIsRoutingDrawerOpen(false);
    } else if (mode === 'dem') {
      setLayerVisibility({ roads: true, manholes: false, substations: false, dem: true, routing: false });
      setIsRoutingDrawerOpen(false);
    } else if (mode === 'routing') {
      setLayerVisibility({ roads: true, manholes: true, substations: true, dem: false, routing: true });
      setIsRoutingDrawerOpen(true);
    }
  };

  // Zoom Helpers
  const handleZoomIn = () => mapInstanceRef.current?.zoomIn();
  const handleZoomOut = () => mapInstanceRef.current?.zoomOut();
  const handleResetView = () => {
    mapInstanceRef.current?.setView(CHENNAI_CENTER, DEFAULT_ZOOM, { animate: true });
  };

  // Initialize Leaflet Map (Created ONCE, never destroyed during zoom)
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    // Standard high-performance Leaflet instance with smooth natural zooming
    const map = L.map(mapContainerRef.current, {
      center: CHENNAI_CENTER,
      zoom: DEFAULT_ZOOM,
      minZoom: 10,
      maxZoom: 17,
      zoomControl: false,
      attributionControl: false,
      zoomAnimation: true,
      fadeAnimation: true,
      markerZoomAnimation: true,
    });

    // Dark Basemap tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19,
      subdomains: 'abcd',
    }).addTo(map);

    // Initialize dedicated Layer Groups
    roadsLayerRef.current = L.layerGroup().addTo(map);
    secondaryRoadsLayerRef.current = L.layerGroup().addTo(map);
    labelsLayerRef.current = L.layerGroup().addTo(map);
    manholesLayerRef.current = L.layerGroup().addTo(map);
    substationsLayerRef.current = L.layerGroup().addTo(map);
    routesLayerRef.current = L.layerGroup().addTo(map);

    // DEM Overlay Image Layer (Exact WGS84 GeoTIFF Bounds from dem_viewer.html)
    const demBounds: L.LatLngBoundsExpression = [
      [12.648572680870833, 79.9470527614598],
      [13.351367475969555, 80.36187022640648]
    ];
    demOverlayRef.current = L.imageOverlay('/data/chennai_dem_overlay.png', demBounds, {
      opacity: 0.70,
      interactive: false,
    });

    mapInstanceRef.current = map;

    setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Sync DEM overlay visibility
  useEffect(() => {
    const map = mapInstanceRef.current;
    const dem = demOverlayRef.current;
    if (!map || !dem) return;

    if (layerVisibility.dem) {
      if (!map.hasLayer(dem)) dem.addTo(map);
    } else {
      if (map.hasLayer(dem)) map.removeLayer(dem);
    }
  }, [layerVisibility.dem]);

  // Main Render Loop: Only runs when timeline or layer toggles change (NEVER on zoom!)
  useEffect(() => {
    const map = mapInstanceRef.current;
    const roadsGroup = roadsLayerRef.current;
    const secondaryGroup = secondaryRoadsLayerRef.current;
    const labelsGroup = labelsLayerRef.current;
    const manholesGroup = manholesLayerRef.current;
    const substationsGroup = substationsLayerRef.current;
    const routesGroup = routesLayerRef.current;

    if (!map || !roadsGroup || !secondaryGroup || !labelsGroup || !manholesGroup || !substationsGroup || !routesGroup) return;

    // Clear previous layers
    roadsGroup.clearLayers();
    secondaryGroup.clearLayers();
    labelsGroup.clearLayers();
    manholesGroup.clearLayers();
    substationsGroup.clearLayers();
    routesGroup.clearLayers();

    const masterData = getMasterFloodData();
    const currentStep = TIMELINE_STEPS[timelineIndex];
    const factor = currentStep.factor;
    const horizonKey = currentStep.key;

    // 1. RENDER CLEAN PRIMARY ARTERIAL NETWORK
    // Pure vector multi-layering for glowing neon effect:
    // Outer: 11px wide at 0.22 opacity
    // Mid: 5px wide at 0.85 opacity
    // Core: 2px wide at 1.0 opacity
    // Scales naturally via Leaflet's vector transform without ANY GPU raster distortion!
    if (layerVisibility.roads) {
      BASELINE_ARTERIALS.forEach((road) => {
        const adjustedSurcharge = Math.min(Math.round(road.surcharge * factor), 100);
        let risk = road.risk;
        if (adjustedSurcharge > 85) risk = 'CRITICAL';
        else if (adjustedSurcharge > 70) risk = 'HIGH';

        const cfg = GLOW_CONFIG[risk];

        // Layer 1: Outer Diffuse Vector Glow (Zero CSS blur filter)
        const outerGlow = L.polyline(road.coords, {
          color: cfg.outer,
          weight: risk === 'CRITICAL' ? 12 : 9,
          opacity: 0.25,
          lineCap: 'round',
          lineJoin: 'round',
          interactive: false,
        });

        // Layer 2: Mid Saturated Neon Beam
        const midBeam = L.polyline(road.coords, {
          color: cfg.mid,
          weight: risk === 'CRITICAL' ? 5.5 : 4,
          opacity: 0.85,
          lineCap: 'round',
          lineJoin: 'round',
          interactive: false,
        });

        // Layer 3: Razor-Sharp Molten Core
        const coreLaser = L.polyline(road.coords, {
          color: cfg.core,
          weight: 2,
          opacity: 1.0,
          lineCap: 'round',
          lineJoin: 'round',
          interactive: true,
        });

        const handleSelect = () => {
          setInspectionData({
            type: 'road',
            title: road.name,
            subtitle: `Category: ${road.category}`,
            badge: {
              text: `${risk} RISK`,
              color: risk === 'CRITICAL' ? 'text-red-400' : 'text-orange-400',
              bg: risk === 'CRITICAL' ? 'bg-red-500/20' : 'bg-orange-500/20',
              border: risk === 'CRITICAL' ? 'border-red-500/40' : 'border-orange-500/40',
            },
            metrics: [
              { label: 'Surcharge Factor', value: `${adjustedSurcharge}%`, highlight: true },
              { label: 'Inundation Depth', value: road.depth },
              { label: 'Surface Flow Rate', value: road.flow },
              { label: 'Drain Capacity', value: risk === 'CRITICAL' ? 'Exceeded' : 'Restricted' },
            ],
            warning: risk === 'CRITICAL' ? 'SURCHARGE ALERT: Hydrostatic backflow detected. Avoid low-lying underpasses.' : undefined,
            source: 'GCC Hydraulic Drain Network',
          });
        };

        coreLaser.on('click', handleSelect);

        coreLaser.bindTooltip(
          `<div class="text-xs font-bold text-white">${road.name}</div>
           <div class="text-[11px] ${risk === 'CRITICAL' ? 'text-red-400' : 'text-cyan-400'}">Surcharge: ${adjustedSurcharge}% (${risk})</div>`,
          { className: 'hud-tooltip', sticky: true }
        );

        roadsGroup.addLayer(outerGlow);
        roadsGroup.addLayer(midBeam);
        roadsGroup.addLayer(coreLaser);
      });

      // Secondary micro-segments rendered with clean, thin 2px lines
      if (masterData?.segments && twinMode === 'inundation') {
        masterData.segments.forEach((seg: FloodSegment) => {
          const depthVal = seg.depths && seg.depths[horizonKey] !== undefined
            ? seg.depths[horizonKey]! * factor
            : (seg.peak_depth || 15) * factor;

          let risk: 'CRITICAL' | 'HIGH' | 'MODERATE' | 'NORMAL' = 'NORMAL';
          if (depthVal >= 30) risk = 'CRITICAL';
          else if (depthVal >= 15) risk = 'HIGH';
          else if (depthVal >= 5) risk = 'MODERATE';

          const cfg = GLOW_CONFIG[risk];

          const poly = L.polyline(seg.coords, {
            color: cfg.mid,
            weight: 2,
            opacity: risk === 'CRITICAL' ? 0.85 : 0.6,
            lineCap: 'round',
            lineJoin: 'round',
          });

          poly.on('click', () => {
            setInspectionData({
              type: 'road',
              title: seg.name,
              subtitle: `Zone: ${seg.zone} | OSM: ${seg.osm_type || seg.road_class}`,
              badge: {
                text: `${risk} RISK`,
                color: risk === 'CRITICAL' ? 'text-red-400' : risk === 'HIGH' ? 'text-orange-400' : 'text-cyan-400',
                bg: risk === 'CRITICAL' ? 'bg-red-500/20' : risk === 'HIGH' ? 'bg-orange-500/20' : 'bg-cyan-500/20',
                border: risk === 'CRITICAL' ? 'border-red-500/40' : risk === 'HIGH' ? 'border-orange-500/40' : 'border-cyan-500/40',
              },
              metrics: [
                { label: 'Flood Depth', value: `${depthVal.toFixed(1)} cm`, highlight: depthVal >= 30 },
                { label: 'Elevation', value: `${seg.elevation}m MSL` },
                { label: 'Pipe Dia', value: `${seg.pipe_dia} mm` },
                { label: 'Clog (μ)', value: `${(seg.mu_clog * 100).toFixed(0)}%` },
              ],
              warning: depthVal >= 30 ? 'CRITICAL: Water depth exceeds vehicle intake.' : undefined,
              source: 'GCC Hydraulic Drain Network',
            });
          });

          secondaryGroup.addLayer(poly);
        });
      }
    }

    // 2. RENDER AREA LABELS (Matching Screenshot Typography)
    AREA_LABELS.forEach((lbl) => {
      const labelIcon = L.divIcon({
        className: 'custom-area-marker',
        html: `<span class="area-text-label">${lbl.name}</span>`,
        iconSize: [120, 20],
        iconAnchor: [60, 10],
      });
      const marker = L.marker(lbl.pos, { icon: labelIcon, interactive: false });
      labelsGroup.addLayer(marker);
    });

    // 3. RENDER 25 HYDRAULIC FOUNTAIN GEYSER MANHOLES
    if (layerVisibility.manholes) {
      const hotspots: HotspotManhole[] = masterData?.hotspots || [
        { id: 'MH_HOTSPOT_01', name: 'Velachery 100ft Road', location: 'Velachery', zone: 'Velachery', lat: 12.9815, lon: 80.2180, elevation: 5.2, hgl: 6.4, backflow_m3s: 0.65, blockage_type: 'Solid Plastic Waste & Silt', source: 'GCC 1913 Civic Portal', confidence: 'High' },
        { id: 'MH_HOTSPOT_02', name: 'T. Nagar Bazullah Road', location: 'T. Nagar', zone: 'Teynampet', lat: 13.0426, lon: 80.2372, elevation: 7.26, hgl: 7.81, backflow_m3s: 0.58, blockage_type: 'Garbage Blocking Drains', source: 'Namma Chennai App', confidence: 'High' },
        { id: 'MH_HOTSPOT_03', name: 'Kodambakkam High Road', location: 'Kodambakkam', zone: 'Kodambakkam', lat: 13.0512, lon: 80.2245, elevation: 7.8, hgl: 8.9, backflow_m3s: 0.72, blockage_type: 'Construction Debris', source: 'GCC 1913 Grievance', confidence: 'High' },
        { id: 'MH_HOTSPOT_04', name: 'Guindy Race Course Outfall', location: 'Guindy', zone: 'Guindy', lat: 13.0070, lon: 80.2030, elevation: 8.5, hgl: 9.6, backflow_m3s: 0.52, blockage_type: 'Siltation in Culvert', source: 'Zone 13 Engineering', confidence: 'Medium' },
      ];

      hotspots.forEach((mh: HotspotManhole) => {
        const fountainIcon = L.divIcon({
          className: 'fountain-geyser-icon',
          html: `
            <div class="fountain-manhole" title="${mh.name}">
              <div class="wave wave-1"></div>
              <div class="wave wave-2"></div>
              <div class="wave wave-3"></div>
              <div class="core"></div>
            </div>
          `,
          iconSize: [22, 22],
          iconAnchor: [11, 11],
        });

        const marker = L.marker([mh.lat, mh.lon || mh.lng!], { icon: fountainIcon });

        marker.on('click', () => {
          setInspectionData({
            type: 'manhole',
            title: mh.name,
            subtitle: `Location: ${mh.location} | Zone: ${mh.zone || 'Central'}`,
            badge: {
              text: 'HYDRAULIC GEYSER SURCHARGE',
              color: 'text-red-400',
              bg: 'bg-red-500/20',
              border: 'border-red-500/40',
            },
            metrics: [
              { label: 'Backflow Discharge', value: `${mh.backflow_m3s || '0.58'} m³/s`, highlight: true },
              { label: 'HGL Hydraulic Head', value: `${mh.hgl}m MSL` },
              { label: 'Ground Elevation', value: `${mh.elevation}m MSL` },
              { label: 'Surcharge Head', value: `+${((mh.hgl - mh.elevation) * 100).toFixed(0)} cm` },
            ],
            warning: `Blockage Cause: ${mh.blockage_type || 'Heavy Siltation & Debris'}`,
            source: mh.source || 'GCC 1913 Civic Portal',
          });
        });

        marker.bindTooltip(
          `<div class="text-xs font-bold text-white">${mh.id}: ${mh.name}</div>
           <div class="text-[11px] text-red-400">Backflow: ${mh.backflow_m3s || 0.55} m³/s (Geyser)</div>`,
          { className: 'hud-tooltip', sticky: true }
        );

        manholesGroup.addLayer(marker);
      });
    }

    // 4. RENDER 20 TNEB ELECTRICAL SUBSTATIONS
    if (layerVisibility.substations) {
      const substations = masterData?.substations || [];

      substations.forEach((ss: Substation) => {
        const isCritical = ss.flood_risk === 'Critical' || ss.flood_risk === 'High';
        const color = isCritical ? '#ff1a40' : '#f59e0b';

        const subIcon = L.divIcon({
          className: 'substation-icon',
          html: `
            <div class="relative flex items-center justify-center w-6 h-6 ${isCritical ? 'substation-critical' : ''}">
              <div class="w-5 h-5 rounded-lg bg-[#0f172a] border border-amber-400/80 flex items-center justify-center shadow-lg">
                <span class="text-[10px] font-black" style="color: ${color}">⚡</span>
              </div>
            </div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 12],
        });

        const marker = L.marker([ss.lat, ss.lon || ss.lng!], { icon: subIcon });

        marker.on('click', () => {
          setInspectionData({
            type: 'substation',
            title: ss.name,
            subtitle: `Type: ${ss.type} | Criticality: ${ss.criticality}`,
            badge: {
              text: `${ss.flood_risk.toUpperCase()} FLOOD RISK`,
              color: isCritical ? 'text-red-400' : 'text-amber-400',
              bg: isCritical ? 'bg-red-500/20' : 'bg-amber-500/20',
              border: isCritical ? 'border-red-500/40' : 'border-amber-500/40',
            },
            metrics: [
              { label: 'Voltage Rating', value: ss.voltage, highlight: true },
              { label: 'Plinth Clearance', value: `${ss.plinth_cm} cm` },
              { label: 'Ground Elevation', value: `${ss.elevation_m}m MSL` },
              { label: 'Grid Status', value: ss.status },
            ],
            warning: isCritical ? `WARNING: Water approaching substation plinth height (${ss.plinth_cm} cm). Trip hazard.` : undefined,
            source: 'TNEB Grid Operations Center',
          });
        });

        marker.bindTooltip(
          `<div class="text-xs font-bold text-white">${ss.name} (${ss.voltage})</div>
           <div class="text-[11px] text-amber-400">Risk: ${ss.flood_risk} | Plinth: ${ss.plinth_cm} cm</div>`,
          { className: 'hud-tooltip', sticky: true }
        );

        substationsGroup.addLayer(marker);
      });
    }

    // 5. RENDER EMERGENCY ROUTING (LAYER 4)
    if (layerVisibility.routing && masterData?.routes) {
      const activeScenario = masterData.routes[activeRoutingScenario];

      if (activeScenario) {
        const directLine = L.polyline(activeScenario.direct, {
          color: '#ef4444',
          weight: 5,
          opacity: 0.9,
          dashArray: '8, 8',
          className: 'route-hazard-glow',
        });
        directLine.bindTooltip(
          `<div class="text-xs font-bold text-red-400">❌ Direct Route (Impassable)</div>
           <div class="text-[11px] text-white">Bottleneck: ${activeScenario.direct_bottleneck_depth_cm} cm (Hydrolock Hazard)</div>`,
          { className: 'hud-tooltip', sticky: true }
        );
        routesGroup.addLayer(directLine);

        const safeLine = L.polyline(activeScenario.safe, {
          color: '#10b981',
          weight: 5,
          opacity: 0.95,
          className: 'route-safe-glow',
        });
        safeLine.bindTooltip(
          `<div class="text-xs font-bold text-emerald-400">✅ Safe Detour Route (100% Clear)</div>
           <div class="text-[11px] text-white">Max Depth: ${activeScenario.safe_max_depth_cm} cm (${activeScenario.safe_corridor})</div>`,
          { className: 'hud-tooltip', sticky: true }
        );
        routesGroup.addLayer(safeLine);

        const originMarker = L.circleMarker(activeScenario.origin_coords, {
          radius: 7,
          color: '#ffffff',
          fillColor: '#ef4444',
          fillOpacity: 1,
          weight: 2,
        }).bindTooltip(`<div class="text-xs font-bold">Origin: ${activeScenario.origin}</div>`, { className: 'hud-tooltip' });

        const destMarker = L.circleMarker(activeScenario.destination_coords, {
          radius: 7,
          color: '#ffffff',
          fillColor: '#10b981',
          fillOpacity: 1,
          weight: 2,
        }).bindTooltip(`<div class="text-xs font-bold">Destination: ${activeScenario.destination}</div>`, { className: 'hud-tooltip' });

        routesGroup.addLayer(originMarker);
        routesGroup.addLayer(destMarker);
      }
    }

    // 6. RENDER DEM TERRAIN DEPRESSIONS (LAYER 1)
    if (layerVisibility.dem) {
      DEM_KEY_POINTS.forEach((pt) => {
        const color = pt.elev < 8 ? '#00d2ff' : pt.elev < 14 ? '#10b981' : pt.elev < 22 ? '#f59e0b' : '#ef4444';
        const demIcon = L.divIcon({
          className: 'dem-pt-icon',
          html: `
            <div class="flex items-center gap-1 bg-[#090e1a]/95 px-2 py-0.5 rounded-full border border-slate-700 shadow-lg cursor-pointer hover:scale-110 transition-transform">
              <span class="w-2 h-2 rounded-full shadow-[0_0_6px_currentColor]" style="background-color: ${color}"></span>
              <span class="text-[10px] font-mono font-bold text-white">${pt.elev}m</span>
            </div>
          `,
          iconSize: [52, 22],
          iconAnchor: [26, 11],
        });

        const marker = L.marker([pt.lat, pt.lon], { icon: demIcon });
        marker.on('click', () => {
          setInspectionData({
            type: 'road',
            title: pt.name,
            subtitle: `Slope: ${pt.slope} | Aspect: ${pt.aspect}`,
            badge: {
              text: `${pt.elev}m MSL ELEVATION`,
              color: 'text-emerald-400',
              bg: 'bg-emerald-500/20',
              border: 'border-emerald-500/40',
            },
            metrics: [
              { label: 'Ground Elevation', value: `${pt.elev}m MSL`, highlight: true },
              { label: 'Terrain Slope', value: pt.slope },
              { label: 'Flow Accumulation', value: pt.acc },
              { label: 'Terrain Risk', value: pt.risk },
            ],
            warning: pt.elev < 8 ? 'LOW-LYING BASIN: High vulnerability to ocean surge & canal backflow.' : undefined,
            source: 'ISRO Cartosat-1 30m Hydro-Conditioned DEM',
          });
        });

        marker.bindTooltip(
          `<div class="text-xs font-bold text-white">${pt.name}</div>
           <div class="text-[11px] text-emerald-400">Elevation: ${pt.elev}m MSL (${pt.risk})</div>`,
          { className: 'hud-tooltip', sticky: true }
        );

        routesGroup.addLayer(marker);
      });
    }
  }, [timelineIndex, layerVisibility, activeRoutingScenario, twinMode]);

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => !prev);
    setTimeout(() => {
      mapInstanceRef.current?.invalidateSize();
    }, 250);
  };

  const masterData = getMasterFloodData();

  return (
    <div
      className={`relative w-full h-full rounded-2xl overflow-hidden border border-slate-800/80 bg-[#070b13] flex flex-col transition-all duration-300 shadow-2xl ${
        isFullscreen ? 'fixed inset-4 z-[9999] rounded-2xl' : ''
      }`}
    >
      {/* Top Map Action Bar */}
      <div className="absolute top-4 right-4 z-[1000] flex items-center gap-2">
        {/* Twin Layers Selector Component */}
        <TwinLayerControl
          activeMode={twinMode}
          onModeChange={handleModeChange}
          visibility={layerVisibility}
          onVisibilityChange={setLayerVisibility}
          isOpen={isLayerMenuOpen}
          onToggleOpen={() => setIsLayerMenuOpen(!isLayerMenuOpen)}
        />

        {/* Fullscreen Button */}
        <button
          onClick={toggleFullscreen}
          title={isFullscreen ? 'Exit Fullscreen' : 'Expand Fullscreen'}
          className="p-2 bg-slate-900/80 hover:bg-slate-800 text-slate-300 hover:text-white rounded-lg border border-slate-700/60 backdrop-blur-md transition-all shadow-lg cursor-pointer"
        >
          {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
        </button>
      </div>

      {/* Floating Zoom & View Controls on Top-Left */}
      <div className="absolute top-4 left-4 z-[1000] flex flex-col gap-1.5 pointer-events-auto">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="w-8 h-8 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/60 backdrop-blur-md flex items-center justify-center shadow-lg transition-all cursor-pointer"
        >
          <Plus className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="w-8 h-8 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/60 backdrop-blur-md flex items-center justify-center shadow-lg transition-all cursor-pointer"
        >
          <Minus className="w-4 h-4" />
        </button>
        <button
          onClick={handleResetView}
          title="Reset View to Chennai"
          className="w-8 h-8 rounded-lg bg-slate-900/80 hover:bg-slate-800 text-slate-200 hover:text-white border border-slate-700/60 backdrop-blur-md flex items-center justify-center shadow-lg transition-all cursor-pointer"
        >
          <RotateCcw className="w-3.5 h-3.5" />
        </button>
      </div>

      {/* Main Leaflet Map Container */}
      <div ref={mapContainerRef} className="flex-1 w-full h-full relative z-0" />

      {/* Vertical Intensity Scale on Right (Exact match to screenshot) */}
      <div className="absolute right-4 top-1/2 -translate-y-1/2 z-[1000] pointer-events-none flex flex-col items-center gap-2 bg-slate-900/70 backdrop-blur-md border border-slate-700/50 p-2.5 rounded-xl shadow-2xl">
        <span className="text-[11px] font-medium text-cyan-400 tracking-wider">Low</span>
        <div className="relative w-2.5 h-44 rounded-full overflow-hidden shadow-inner flex flex-col justify-between py-0.5 items-center">
          <div
            className="absolute inset-0 rounded-full"
            style={{
              background: 'linear-gradient(to bottom, #00d2ff 0%, #ffea00 30%, #ff3b30 65%, #ff0055 85%, #00d2ff 100%)',
              boxShadow: '0 0 10px rgba(255, 59, 48, 0.5)'
            }}
          />
          <div
            className="relative z-10 w-4 h-1 bg-white rounded-full shadow-[0_0_6px_#fff] transition-all duration-500"
            style={{
              transform: `translateY(${(timelineIndex / (TIMELINE_STEPS.length - 1)) * 140}px)`,
            }}
          />
        </div>
        <span className="text-[11px] font-medium text-cyan-400 tracking-wider">low</span>
      </div>

      {/* Emergency Routing Drawer Component */}
      {isRoutingDrawerOpen && masterData?.routes && (
        <EmergencyRoutingDrawer
          scenarios={masterData.routes}
          activeScenarioKey={activeRoutingScenario}
          onSelectScenario={setActiveRoutingScenario}
          onClose={() => setIsRoutingDrawerOpen(false)}
        />
      )}

      {/* Asset Inspection Modal Component */}
      {inspectionData && (
        <InspectionDetailModal
          data={inspectionData}
          onClose={() => setInspectionData(null)}
        />
      )}

      {/* Bottom Floating Timeline Scrubber Bar (Exact match to screenshot) */}
      <div className="absolute bottom-5 left-1/2 -translate-x-1/2 z-[1000] w-[88%] max-w-xl bg-slate-900/80 backdrop-blur-lg border border-slate-700/60 px-5 py-2.5 rounded-full shadow-2xl flex items-center gap-4">
        {/* Play / Pause */}
        <button
          onClick={() => setIsPlaying(!isPlaying)}
          title={isPlaying ? 'Pause Simulation' : 'Play Simulation'}
          className="w-7 h-7 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors flex-shrink-0 cursor-pointer"
        >
          {isPlaying ? <Pause className="w-3.5 h-3.5 fill-white" /> : <Play className="w-3.5 h-3.5 fill-white ml-0.5" />}
        </button>

        {/* Scrubber Track */}
        <div className="flex-1 relative flex items-center">
          <div className="w-full h-1 bg-slate-700/70 rounded-full relative">
            <div
              className="h-full bg-cyan-400/80 rounded-full transition-all duration-300"
              style={{
                width: `${(timelineIndex / (TIMELINE_STEPS.length - 1)) * 100}%`,
              }}
            />
            <div className="absolute inset-0 flex justify-between items-center pointer-events-none px-0.5">
              {TIMELINE_STEPS.map((step, idx) => (
                <div
                  key={step.label}
                  className={`w-1.5 h-1.5 rounded-full transition-all ${
                    idx <= timelineIndex ? 'bg-cyan-300 shadow-[0_0_6px_#22d3ee]' : 'bg-slate-600'
                  }`}
                />
              ))}
            </div>
          </div>

          <input
            type="range"
            min={0}
            max={TIMELINE_STEPS.length - 1}
            step={1}
            value={timelineIndex}
            onChange={(e) => setTimelineIndex(Number(e.target.value))}
            className="absolute inset-0 w-full opacity-0 cursor-pointer h-6 -top-2.5 z-20"
          />

          <div
            className="absolute w-3.5 h-3.5 rounded-full bg-white shadow-[0_0_8px_#ffffff,0_0_14px_#22d3ee] pointer-events-none transition-all duration-300 -translate-x-1/2"
            style={{
              left: `${(timelineIndex / (TIMELINE_STEPS.length - 1)) * 100}%`,
            }}
          />
        </div>

        {/* Horizon Indicator */}
        <div className="text-[11px] font-medium text-slate-300 whitespace-nowrap min-w-[54px] text-right">
          <span className="text-cyan-400 font-bold">{TIMELINE_STEPS[timelineIndex].label}</span>{' '}
          <span className="text-slate-400 text-[10px]">({TIMELINE_STEPS[timelineIndex].sub})</span>
        </div>
      </div>

      {/* Embedded CSS */}
      <style>{`
        .leaflet-container {
          background-color: #070b13 !important;
          font-family: inherit;
        }
        .area-text-label {
          font-size: 11px;
          font-weight: 700;
          letter-spacing: 0.12em;
          color: #cbd5e1;
          text-shadow: 0 0 4px #000, 0 0 10px #000, 0 0 14px rgba(0, 0, 0, 0.9);
          text-transform: uppercase;
          pointer-events: none;
          user-select: none;
          white-space: nowrap;
        }
        .hud-tooltip {
          background-color: rgba(15, 23, 42, 0.94) !important;
          backdrop-filter: blur(8px);
          border: 1px solid rgba(51, 65, 85, 0.8) !important;
          border-radius: 8px !important;
          color: white !important;
          box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6) !important;
          padding: 6px 10px !important;
        }
        .hud-tooltip:before {
          border-top-color: rgba(15, 23, 42, 0.94) !important;
        }
      `}</style>
    </div>
  );
}
