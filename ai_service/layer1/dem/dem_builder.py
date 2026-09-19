"""Layer 1: DEM Builder Module - Cartosat-1, SRTM & InSAR Subsidence Fusion.

Responsible for:
  1. Merging ISRO Cartosat-1 30m N12 and N13 DEM tiles.
  2. Converting ellipsoidal heights (h) to orthometric elevation above Mean Sea Level (MSL: H = h - N_geoid).
     Chennai regional EGM96 geoid undulation N_geoid ~ -98.5 meters.
  3. Metric reprojection to UTM Zone 44N (EPSG:32644) with 30m cell resolution.
  4. Void-filling, ocean masking, and InSAR coastal subsidence rate adjustment.
"""

import logging
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, List

import numpy as np
import geopandas as gpd
from shapely.geometry import box
from scipy import ndimage

import rasterio
from rasterio.merge import merge
from rasterio.warp import reproject, Resampling

logger = logging.getLogger(__name__)

DEFAULT_CHENNAI_BOUNDS_WGS84 = (79.95, 12.65, 80.36, 13.35)  # (min_lon, min_lat, max_lon, max_lat)
DEFAULT_UTM_CRS = "EPSG:32644"
DEFAULT_PIXEL_RES_M = 30.0

# Regional Geoid Undulation (EGM96/EGM2008 offset for Chennai Region)
# Cartosat-1 raw products are referenced to WGS84 ellipsoid. Orthometric MSL H = h - N
CHENNAI_GEOID_OFFSET_M = 98.5


def find_or_extract_file(base_dir: Path, filename_pattern: str, zip_path: Optional[Path] = None) -> Path:
    """Find file in Datasets directory recursively or auto-extract from zip archives."""
    datasets_dir = base_dir / "Datasets"
    # 1. Search for existing uncompressed file
    for p in datasets_dir.rglob(filename_pattern):
        if p.is_file() and p.stat().st_size > 1000:
            return p

    # 2. Check all zip archives in Datasets and Google_Drive_Datasets
    potential_zips = [zip_path] if zip_path and zip_path.exists() else []
    potential_zips.extend(list(datasets_dir.rglob("*.zip")))
    gdrive_dir = base_dir / "Google_Drive_Datasets"
    if gdrive_dir.exists():
        potential_zips.extend(list(gdrive_dir.rglob("*.zip")))

    for z_file in potential_zips:
        if z_file and z_file.is_file():
            extract_target = z_file.parent / "extracted"
            extract_target.mkdir(parents=True, exist_ok=True)
            try:
                with zipfile.ZipFile(z_file, 'r') as z:
                    for name in z.namelist():
                        if name.endswith(filename_pattern):
                            z.extract(name, extract_target)
                            candidate = extract_target / name
                            if candidate.exists() and candidate.stat().st_size > 1000:
                                return candidate
            except Exception as e:
                logger.debug("Could not read zip %s: %s", z_file, e)

    raise FileNotFoundError(f"Could not locate '{filename_pattern}' in {datasets_dir} or any zip archive")


class DEMBuilder:
    """Builds, calibrates, and reprojects base elevation rasters for Greater Chennai Corporation."""

    def __init__(self,
                 extracted_dir: Optional[Path] = None,
                 output_dir: Optional[Path] = None,
                 base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).resolve().parent.parent.parent.parent
        self.datasets_dir = self.base_dir / "Datasets"
        self.output_dir = output_dir or (self.datasets_dir / "processed_dem")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def create_cartosat_mosaic(self) -> Tuple[np.ndarray, rasterio.Affine, Dict[str, Any]]:
        """Merge Cartosat-1 N12 and N13 tiles into single seamless WGS84 raster."""
        zip_terrain = self.datasets_dir / "03_Terrain_and_DEM_Vijay" / "terrain data(Vijay).zip"
        
        tif1 = find_or_extract_file(self.base_dir, "P5_PAN_CD_N12_000_E080_000_DEM_30m.tif", zip_terrain)
        tif2 = find_or_extract_file(self.base_dir, "P5_PAN_CD_N13_000_E080_000_DEM_30m.tif", zip_terrain)

        with rasterio.open(tif1) as s1, rasterio.open(tif2) as s2:
            mosaic, out_trans = merge([s1, s2], nodata=-32768.0)
            meta = s1.meta.copy()
            meta.update({
                "height": mosaic.shape[1],
                "width": mosaic.shape[2],
                "transform": out_trans,
                "nodata": -32768.0,
                "dtype": "float32"
            })

        mosaic_path = self.output_dir / "chennai_cartosat_wgs84_mosaic.tif"
        with rasterio.open(mosaic_path, "w", **meta) as dest:
            dest.write(mosaic.astype(np.float32))

        logger.info("Created Cartosat-1 mosaic at %s: shape %s", mosaic_path, mosaic.shape)
        return mosaic[0], out_trans, meta

    def reproject_to_utm(
        self,
        src_path: Optional[Path] = None,
        dst_crs: str = DEFAULT_UTM_CRS,
        resolution_m: float = DEFAULT_PIXEL_RES_M,
        bounds_wgs84: Tuple[float, float, float, float] = DEFAULT_CHENNAI_BOUNDS_WGS84,
        apply_insar_subsidence: bool = True
    ) -> Tuple[np.ndarray, rasterio.Affine, Dict[str, Any]]:
        """Reproject mosaic to UTM 44N metric grid, apply geoid offset & InSAR subsidence."""
        if src_path is None:
            src_path = self.output_dir / "chennai_cartosat_wgs84_mosaic.tif"
            if not src_path.exists():
                self.create_cartosat_mosaic()

        with rasterio.open(src_path) as src:
            bbox_poly = box(*bounds_wgs84)
            gdf_bbox = gpd.GeoDataFrame({"geometry": [bbox_poly]}, crs="EPSG:4326")
            gdf_utm = gdf_bbox.to_crs(dst_crs)
            minx, miny, maxx, maxy = gdf_utm.total_bounds

            dst_width = int(np.ceil((maxx - minx) / resolution_m))
            dst_height = int(np.ceil((maxy - miny) / resolution_m))
            dst_transform = rasterio.transform.from_origin(minx, maxy, resolution_m, resolution_m)

            destination = np.full((dst_height, dst_width), -9999.0, dtype=np.float32)

            reproject(
                source=rasterio.band(src, 1),
                destination=destination,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=dst_transform,
                dst_crs=dst_crs,
                resampling=Resampling.bilinear,
                src_nodata=src.nodata,
                dst_nodata=-9999.0
            )

        # 1. EGM96 Geoid Calibration (Orthometric Height: H = h - N)
        valid_mask = (destination > -100.0) & (destination < 2000.0)
        destination[valid_mask] = destination[valid_mask] - CHENNAI_GEOID_OFFSET_M

        # 2. InSAR Subsidence Adjustment
        if apply_insar_subsidence:
            destination = self._apply_insar_subsidence(destination, dst_transform, dst_crs)

        # 3. Clean low coastal elevations (avoid -9999 artifacts in urban floodplain)
        destination[~valid_mask] = 0.0
        destination = np.maximum(0.0, destination)

        # Fill voids with morphological Gaussian filter
        mask_voids = (destination <= 0.0)
        if np.any(mask_voids):
            smoothed = ndimage.gaussian_filter(destination, sigma=1.0)
            destination[mask_voids] = smoothed[mask_voids]

        out_meta = {
            "driver": "GTiff",
            "height": dst_height,
            "width": dst_width,
            "count": 1,
            "dtype": "float32",
            "crs": dst_crs,
            "transform": dst_transform,
            "nodata": -9999.0
        }

        dst_path = self.output_dir / "chennai_dem_utm44n_30m.tif"
        with rasterio.open(dst_path, "w", **out_meta) as dest:
            dest.write(destination, 1)

        logger.info("Reprojected DEM to %s (%s): %dx%d cells", dst_path, dst_crs, dst_width, dst_height)
        return destination, dst_transform, out_meta

    def _apply_insar_subsidence(
        self,
        dem: np.ndarray,
        transform: rasterio.Affine,
        crs: str
    ) -> np.ndarray:
        """Applies InSAR coastal subsidence rates (mm/yr) over elapsed years."""
        sub_csv = self.datasets_dir / "chennai_unified_flood_master_dataset.csv"
        if not sub_csv.exists():
            return dem

        try:
            import pandas as pd
            df = pd.read_csv(sub_csv)
            if "insar_subsidence_mm_year" not in df.columns:
                return dem

            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326")
            gdf_utm = gdf.to_crs(crs)

            # Cumulative subsidence over 5 years (2021 to 2026) in meters
            inv_trans = ~transform
            corrected_dem = dem.copy()
            h, w = dem.shape

            for _, row in gdf_utm.iterrows():
                rate_mm = row.get("insar_subsidence_mm_year", 0.0)
                if rate_mm > 0:
                    pt = row.geometry
                    col, r = inv_trans @ (pt.x, pt.y)
                    r_idx, c_idx = int(round(r)), int(round(col))
                    if 0 <= r_idx < h and 0 <= c_idx < w:
                        offset_m = (rate_mm * 5.0) / 1000.0
                        corrected_dem[r_idx, c_idx] = max(0.0, corrected_dem[r_idx, c_idx] - offset_m)

            logger.info("Applied InSAR subsidence adjustment to %d control points", len(gdf_utm))
            return corrected_dem
        except Exception as e:
            logger.warning("Could not apply InSAR subsidence: %s", e)
            return dem
