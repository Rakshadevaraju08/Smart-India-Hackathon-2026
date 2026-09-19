import os
import numpy as np
import rasterio
from rasterio.transform import from_bounds
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("obtain_dem")

DEM_PATH = 'ai_service/layer4/data/raw/chennai_dem_synthetic.tif'

def generate_synthetic_dem():
    os.makedirs(os.path.dirname(DEM_PATH), exist_ok=True)
    
    # Chennai Bounding Box
    min_lon, min_lat = 80.0, 12.8
    max_lon, max_lat = 80.4, 13.3
    
    # Resolution: 30m is approx 0.00027 degrees
    res = 0.00027
    width = int((max_lon - min_lon) / res)
    height = int((max_lat - min_lat) / res)
    
    logger.info(f"Generating synthetic DEM raster {width}x{height}...")
    
    # Chennai generally slopes up from the coast (East, lon ~80.3) to inland (West, lon ~80.0)
    # Coastal elevation ~2m, inland ~25m
    lon_grid = np.linspace(min_lon, max_lon, width)
    
    # Create elevation array
    elevation = np.zeros((height, width), dtype=np.float32)
    
    for x, lon in enumerate(lon_grid):
        # Normalized distance from coast (0 at coast, 1 inland)
        # Coast is at roughly 80.3, inland 80.0
        dist_from_coast = max(0.0, min(1.0, (80.3 - lon) / 0.3))
        
        # Elevation formula: 2m at coast, rising to 25m inland
        elev = 2.0 + (dist_from_coast * 23.0)
        
        # Add a tiny bit of random noise
        elev += np.random.normal(0, 0.5)
        
        elevation[:, x] = max(0.0, elev)
        
    transform = from_bounds(min_lon, min_lat, max_lon, max_lat, width, height)
    
    with rasterio.open(
        DEM_PATH,
        'w',
        driver='GTiff',
        height=height,
        width=width,
        count=1,
        dtype=elevation.dtype,
        crs='+proj=latlong',
        transform=transform,
    ) as dst:
        dst.write(elevation, 1)
        
    logger.info(f"Successfully generated synthetic GeoTIFF at {DEM_PATH}")

if __name__ == "__main__":
    generate_synthetic_dem()
