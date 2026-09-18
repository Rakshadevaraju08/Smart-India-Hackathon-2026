/**
 * Hydraulics, Manhole Surcharge & Coastal Tidal Route
 * MoES / NCMRWF Problem Statement #26085
 */
const express = require('express');
const router = express.Router();
const db = require('../db');

router.get('/', async (req, res) => {
  try {
    const clogging = Math.min(0.85, Math.max(0.0, parseFloat(req.query.clogging) || 0.35));
    const tideHour = parseFloat(req.query.tide_hour) || 2.0;

    // Bay of Bengal semi-diurnal astronomical tide calculation
    const m2Head = 0.42 * Math.cos((2 * Math.PI / 12.42) * tideHour);
    const s2Head = 0.18 * Math.cos((2 * Math.PI / 12.0) * tideHour);
    const surgeHead = 0.35; // Cyclone Michaung storm surge offset
    const coastalTidalStageM = +(m2Head + s2Head + surgeHead).toFixed(2);

    // Fetch from database
    const manholes = await db.getManholes(clogging, coastalTidalStageM);

    res.json({
      status: 'operational',
      standards: 'CPHEEO Manual on Stormwater Drainage & IRC:SP:50',
      clogging_factor_applied: clogging,
      coastal_boundary: {
        sea_basin: 'Bay of Bengal',
        astronomical_harmonics: 'M2 + S2 Semidiurnal',
        tidal_stage_m: coastalTidalStageM,
        backwater_throttling_active: coastalTidalStageM > 0.75,
        impacted_outfalls: ['Adyar Estuary', 'Cooum River Mouth', 'Buckingham Canal', 'Ennore Creek']
      },
      conduit_hierarchy: {
        arterial_trunk_canals_mm: 1800,
        sub_arterial_drains_mm: 1200,
        collector_drains_mm: 900,
        local_street_branches_mm: 600
      },
      hotspot_manholes: manholes
    });
  } catch (error) {
    console.error("Hydraulics route error:", error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

module.exports = router;
