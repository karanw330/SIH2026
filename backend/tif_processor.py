import os
import glob
import json
import math
from typing import Dict, Any, Optional, Tuple

# Try importing GIS & Imaging raster libraries
HAS_RASTERIO = False
try:
    import rasterio
    from rasterio.warp import transform_bounds, transform
    HAS_RASTERIO = True
except ImportError:
    HAS_RASTERIO = False

HAS_TIFFFILE = False
try:
    import tifffile
    HAS_TIFFFILE = True
except ImportError:
    HAS_TIFFFILE = False

HAS_GDAL = False
try:
    from osgeo import gdal, osr
    HAS_GDAL = True
except ImportError:
    HAS_GDAL = False

HAS_NUMPY = False
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

HAS_PIL = False
try:
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class GeoTIFFProcessor:
    def __init__(self, root_dir: str):
        self.root_dir = root_dir
        self.cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.tif_path: Optional[str] = None
        self.bounds: Optional[list] = None  # [[south, west], [north, east]]
        self.extent_bbox: Optional[list] = None  # [west, south, east, north]
        self.raster_data = None
        self.transform = None
        self.crs = None
        self.min_val = 0.0
        self.max_val = 1.0
        self.mean_val = 0.0
        self.is_loaded = False

    def find_tif_file(self) -> Optional[str]:
        """Scans root directory for any .tif or .tiff files."""
        search_patterns = [
            os.path.join(self.root_dir, "*.tif"),
            os.path.join(self.root_dir, "*.tiff"),
            os.path.join(self.root_dir, "ner_*.tif"),
            os.path.join(self.root_dir, "*", "*.tif")
        ]
        for pattern in search_patterns:
            matches = glob.glob(pattern)
            if matches:
                for m in matches:
                    low = m.lower()
                    if "ner_" in low or "ilsm" in low or "landslide" in low or "suscept" in low or "hazard" in low:
                        return m
                return matches[0]
        return None

    def get_risk_category(self, score: float) -> Tuple[str, str]:
        """Returns risk level string and hex color for continuous float score 0.0 to 1.0."""
        if score < 0.25:
            return "Stable Terrain / Basins", "#1a9641"  # Green
        elif score < 0.50:
            return "Moderate Slope / Low Risk", "#ffffbf"  # Yellow
        elif score < 0.75:
            return "High Risk (Monitor Closely)", "#fdae61" # Orange
        else:
            return "Critical Hazard Risk", "#d7191c"       # Strict Red Severe Corridor

    def clean_and_normalize_raster(self, raw_arr: np.ndarray) -> np.ndarray:
        """Filters nodata/nan/inf values and normalizes array values into [0.0, 1.0]."""
        valid_mask = np.isfinite(raw_arr) & (raw_arr >= 0.0) & (raw_arr < 1e5)
        clean = np.zeros_like(raw_arr, dtype=np.float32)
        clean[valid_mask] = raw_arr[valid_mask]

        if not np.any(valid_mask):
            print("⚠️ Warning: No valid positive pixels found in raster array.")
            return clean

        pos_pixels = clean[clean > 0.0]
        if len(pos_pixels) == 0:
            print("ℹ️ Raster array contains all zero values.")
            return clean

        min_pos = float(np.min(pos_pixels))
        max_pos = float(np.max(pos_pixels))
        print(f"📊 Raster Pixel Stats -> Non-zero Pixels: {len(pos_pixels):,}, Min: {min_pos:.4f}, Max: {max_pos:.4f}")

        if max_pos > 1.0 and max_pos <= 100.0:
            clean = clean / 100.0
            print("🔄 Normalized raster values from [0, 100] to [0.0, 1.0]")
        elif max_pos > 100.0:
            clean = clean / max_pos
            print(f"🔄 Normalized raster values from [0, {max_pos:.1f}] to [0.0, 1.0]")

        return np.clip(clean, 0.0, 1.0)

    def load_and_process(self) -> Dict[str, Any]:
        """Loads GeoTIFF file and generates colorized PNG overlay + metadata."""
        tif_file = self.find_tif_file()
        if not tif_file:
            print("ℹ️ No .tif file found in project root yet. Generating default North East region bounds for readiness.")
            self.bounds = [[21.5, 89.5], [29.5, 97.5]]
            self.extent_bbox = [89.5, 21.5, 97.5, 29.5]
            return {
                "status": "ready_for_tif",
                "message": "Place your .tif file in the project root directory.",
                "bounds": self.bounds,
                "extent": self.extent_bbox,
                "has_raster": False
            }

        self.tif_path = tif_file
        print(f"🌲 Loading & Analyzing GeoTIFF: {self.tif_path}")

        # 1. Method A: Rasterio (Gold Standard)
        if HAS_RASTERIO and HAS_NUMPY:
            try:
                print("⚡ Reading GeoTIFF via Rasterio GIS engine...")
                with rasterio.open(self.tif_path) as src:
                    self.crs = src.crs
                    raw_band = src.read(1)
                    band1 = self.clean_and_normalize_raster(raw_band)
                    
                    self.raster_data = band1
                    self.transform = src.transform
                    
                    b = src.bounds
                    if src.crs and str(src.crs).lower() != "epsg:4326":
                        try:
                            w, s, e, n = transform_bounds(src.crs, "EPSG:4326", b.left, b.bottom, b.right, b.top)
                        except Exception:
                            w, s, e, n = b.left, b.bottom, b.right, b.top
                    else:
                        w, s, e, n = b.left, b.bottom, b.right, b.top
                    
                    if w > 180 or n > 90 or s < -90 or e < -180:
                        w, s, e, n = 89.5, 21.5, 97.5, 29.5

                    self.extent_bbox = [w, min(s, n), e, max(s, n)]
                    self.bounds = [[min(s, n), w], [max(s, n), e]]
                    
                    valid_mask = band1 > 0.001
                    if np.any(valid_mask):
                        self.min_val = float(np.min(band1[valid_mask]))
                        self.max_val = float(np.max(band1[valid_mask]))
                        self.mean_val = float(np.mean(band1[valid_mask]))
                    
                    self.generate_png_overlay(band1)
                    self.is_loaded = True
                    return self._build_loaded_response()
            except Exception as re:
                print(f"⚠️ Rasterio load note: {re}")

        # 2. Method B: tifffile (Specialized GeoTIFF & BigTIFF Reader)
        if HAS_TIFFFILE and HAS_NUMPY:
            try:
                print("🔬 Reading GeoTIFF via tifffile engine...")
                with tifffile.TiffFile(self.tif_path) as tf:
                    page = tf.pages[0]
                    raw_band = page.asarray().astype(np.float32)
                    if raw_band.ndim > 2:
                        raw_band = raw_band[:, :, 0]
                    
                    band1 = self.clean_and_normalize_raster(raw_band)
                    self.raster_data = band1
                    
                    w, s, e, n = 89.5, 21.5, 97.5, 29.5
                    try:
                        tags = page.tags
                        if 'ModelPixelScaleTag' in tags and 'ModelTiepointTag' in tags:
                            scale_x, scale_y = tags['ModelPixelScaleTag'].value[:2]
                            tp_x, tp_y = tags['ModelTiepointTag'].value[3:5]
                            if -180 <= tp_x <= 180 and -90 <= tp_y <= 90:
                                w = tp_x
                                n = tp_y
                                e = w + page.shape[1] * scale_x
                                s = n - page.shape[0] * scale_y
                    except Exception:
                        pass

                    self.extent_bbox = [w, min(s, n), e, max(s, n)]
                    self.bounds = [[min(s, n), w], [max(s, n), e]]

                    valid_mask = band1 > 0.001
                    if np.any(valid_mask):
                        self.min_val = float(np.min(band1[valid_mask]))
                        self.max_val = float(np.max(band1[valid_mask]))
                        self.mean_val = float(np.mean(band1[valid_mask]))

                    self.generate_png_overlay(band1)
                    self.is_loaded = True
                    return self._build_loaded_response()
            except Exception as te:
                print(f"⚠️ tifffile load note: {te}")

        # 3. Method C: GDAL
        if HAS_GDAL and HAS_NUMPY:
            try:
                print("🗺️ Reading GeoTIFF via GDAL engine...")
                ds = gdal.Open(self.tif_path)
                if ds:
                    band = ds.GetRasterBand(1)
                    raw_band = band.ReadAsArray().astype(np.float32)
                    band1 = self.clean_and_normalize_raster(raw_band)

                    self.raster_data = band1
                    gt = ds.GetGeoTransform()
                    w = gt[0]
                    n = gt[3]
                    e = w + ds.RasterXSize * gt[1]
                    s = n + ds.RasterYSize * gt[5]
                    
                    if w > 180 or n > 90 or s < -90 or e < -180:
                        w, s, e, n = 89.5, 21.5, 97.5, 29.5
                    
                    self.extent_bbox = [w, min(s, n), e, max(s, n)]
                    self.bounds = [[min(s, n), w], [max(s, n), e]]

                    valid_mask = band1 > 0.001
                    if np.any(valid_mask):
                        self.min_val = float(np.min(band1[valid_mask]))
                        self.max_val = float(np.max(band1[valid_mask]))
                        self.mean_val = float(np.mean(band1[valid_mask]))

                    self.generate_png_overlay(band1)
                    self.is_loaded = True
                    return self._build_loaded_response()
            except Exception as ge:
                print(f"⚠️ GDAL load note: {ge}")

        # 4. Method D: Pillow (PIL)
        if HAS_PIL:
            try:
                print("📷 Reading GeoTIFF via Pillow (PIL) engine...")
                img = Image.open(self.tif_path)
                if HAS_NUMPY:
                    raw_arr = np.array(img, dtype=np.float32)
                    if raw_arr.ndim > 2:
                        raw_arr = raw_arr[:, :, 0]
                    
                    arr = self.clean_and_normalize_raster(raw_arr)
                    self.raster_data = arr
                    
                    w, s, e, n = 89.5, 21.5, 97.5, 29.5
                    self.extent_bbox = [w, min(s, n), e, max(s, n)]
                    self.bounds = [[min(s, n), w], [max(s, n), e]]
                    
                    valid_mask = arr > 0.001
                    if np.any(valid_mask):
                        self.min_val = float(np.min(arr[valid_mask]))
                        self.max_val = float(np.max(arr[valid_mask]))
                        self.mean_val = float(np.mean(arr[valid_mask]))

                    self.generate_png_overlay(arr)
                    self.is_loaded = True
                    return self._build_loaded_response()
            except Exception as pe:
                print(f"❌ PIL fallback note: {pe}")

        print("❌ Warning: None of the GeoTIFF engines (rasterio, tifffile, gdal, PIL) could read the file. Please install rasterio or tifffile: pip install rasterio tifffile")
        self.bounds = [[21.5, 89.5], [29.5, 97.5]]
        self.extent_bbox = [89.5, 21.5, 97.5, 29.5]
        self.is_loaded = True
        return {
            "status": "missing_dependencies",
            "file": os.path.basename(self.tif_path),
            "bounds": self.bounds,
            "extent": self.extent_bbox,
            "has_raster": False
        }

    def _build_loaded_response(self) -> Dict[str, Any]:
        return {
            "status": "active",
            "file": os.path.basename(self.tif_path) if self.tif_path else None,
            "bounds": self.bounds,
            "extent": self.extent_bbox,
            "shape": list(self.raster_data.shape) if self.raster_data is not None else [],
            "stats": {
                "min_susceptibility": round(self.min_val, 4),
                "max_susceptibility": round(self.max_val, 4),
                "mean_susceptibility": round(self.mean_val, 4)
            },
            "has_raster": True
        }

    def generate_png_overlay(self, arr: np.ndarray) -> str:
        """Generates continuous 256-color gradient RGBA PNG for map overlay."""
        png_path = os.path.join(self.cache_dir, "landslide_overlay.png")
        if not HAS_PIL or not HAS_NUMPY:
            return png_path

        try:
            h, w = arr.shape
            max_dim = 2048
            if h > max_dim or w > max_dim:
                scale = max_dim / float(max(h, w))
                new_h, new_w = int(h * scale), int(w * scale)
                img_temp = Image.fromarray(arr.astype(np.float32))
                img_resized = img_temp.resize((new_w, new_h), Image.BILINEAR)
                arr = np.array(img_resized)
                h, w = arr.shape

            # Exact 4-Class Scientific Palette Mapping
            # 0.00 - 0.25: Green #1a9641 (26, 150, 65) -> Dominating baseline
            # 0.25 - 0.50: Yellow #ffffbf (255, 255, 191) -> Low risk
            # 0.50 - 0.75: Orange #fdae61 (253, 174, 97) -> High risk
            # 0.75 - 1.00: Red #d7191c (215, 25, 28) -> Critical Severe Corridor
            lut = np.zeros((256, 4), dtype=np.uint8)
            for i in range(256):
                t = i / 255.0
                if t < 0.005:
                    lut[i] = [0, 0, 0, 0]  # Fully transparent background zero pixels
                elif t < 0.25:
                    # 1. Green #1a9641 baseline
                    factor = (t - 0.005) / 0.245
                    r = int(26 + factor * (100 - 26))
                    g = int(150 + factor * (180 - 150))
                    b = int(65 + factor * (80 - 65))
                    lut[i] = [r, g, b, 130] # Soft dominating green
                elif t < 0.50:
                    # 2. Green #1a9641 -> Yellow #ffffbf
                    factor = (t - 0.25) / 0.25
                    r = int(26 + factor * (255 - 26))
                    g = int(150 + factor * (255 - 150))
                    b = int(65 + factor * (191 - 65))
                    lut[i] = [r, g, b, 170]
                elif t < 0.75:
                    # 3. Yellow #ffffbf -> Orange #fdae61
                    factor = (t - 0.50) / 0.25
                    r = int(255 + factor * (253 - 255))
                    g = int(255 + factor * (174 - 255))
                    b = int(191 + factor * (97 - 191))
                    lut[i] = [r, g, b, 205]
                else:
                    # 4. Orange #fdae61 -> Red #d7191c (Strict Critical Red)
                    factor = (t - 0.75) / 0.25
                    r = int(253 + factor * (215 - 253))
                    g = int(174 + factor * (25 - 174))
                    b = int(97 + factor * (28 - 97))
                    lut[i] = [r, g, b, 240]

            indices = np.clip((arr * 255.0).astype(np.int32), 0, 255)
            rgba = lut[indices]

            img = Image.fromarray(rgba, "RGBA")
            img.save(png_path, "PNG", optimize=True)
            print(f"✨ Smooth continuous color gradient PNG overlay generated at: {png_path}")
            return png_path
        except Exception as pe:
            print(f"❌ Failed to generate PNG overlay: {pe}")
            return png_path

    def query_susceptibility(self, lat: float, lon: float) -> Dict[str, Any]:
        """Queries exact continuous probability score for lat/lon coordinate."""
        if not self.is_loaded or self.raster_data is None or not HAS_NUMPY:
            base_score = (math.sin(lat * 3.5) * math.cos(lon * 2.5) + 1.0) / 2.0
            base_score = round(max(0.01, min(0.98, base_score)), 4)
            cat, col = self.get_risk_category(base_score)
            return {
                "latitude": lat,
                "longitude": lon,
                "probability_score": base_score,
                "percentage": f"{round(base_score * 100, 2)}%",
                "risk_category": cat,
                "color": col,
                "mode": "simulated"
            }

        try:
            if self.extent_bbox and len(self.extent_bbox) == 4:
                w, s, e, n = self.extent_bbox
                min_lat, max_lat = min(s, n), max(s, n)
                min_lon, max_lon = min(w, e), max(w, e)

                if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                    h, width = self.raster_data.shape
                    row = int((max_lat - lat) / (max_lat - min_lat) * h)
                    col = int((lon - min_lon) / (max_lon - min_lon) * width)
                    row = max(0, min(h - 1, row))
                    col = max(0, min(width - 1, col))

                    val = float(self.raster_data[row, col])
                    val = max(0.0, min(1.0, val))
                    cat, col_hex = self.get_risk_category(val)
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "probability_score": round(val, 4),
                        "percentage": f"{round(val * 100, 2)}%",
                        "risk_category": cat,
                        "color": col_hex,
                        "mode": "raster_pixel_exact"
                    }

            return {
                "latitude": lat,
                "longitude": lon,
                "probability_score": 0.0,
                "percentage": "0.0%",
                "risk_category": "Outside Raster Area",
                "color": "#64748b",
                "mode": "out_of_bounds"
            }
        except Exception as qe:
            print(f"Error querying raster coordinate: {qe}")
            return {
                "latitude": lat,
                "longitude": lon,
                "probability_score": 0.0,
                "percentage": "0.0%",
                "risk_category": "Query Error",
                "color": "#64748b",
                "mode": "error"
            }


# Singleton instance
root_workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
tif_processor = GeoTIFFProcessor(root_dir=root_workspace)
