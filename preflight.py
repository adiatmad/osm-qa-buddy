import json
import os
import subprocess

from shapely.geometry import mapping, shape
from shapely.ops import unary_union


def _load_features(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    geojson_type = data.get("type")
    if geojson_type == "Feature":
        features = [data]
    elif geojson_type == "FeatureCollection":
        features = data.get("features", [])
    elif geojson_type in ("Polygon", "MultiPolygon"):
        features = [{"type": "Feature", "properties": {}, "geometry": data}]
    else:
        raise ValueError("GeoJSON must be a Feature, FeatureCollection, Polygon, or MultiPolygon.")

    if not features:
        raise ValueError("GeoJSON contains no features.")

    for feature in features:
        geometry = feature.get("geometry")
        if not geometry:
            raise ValueError("GeoJSON contains a feature without geometry.")
        shape(geometry)

    return data, features


def _polygon_union(features, label):
    geometries = []
    for feature in features:
        geom = shape(feature["geometry"])
        if geom.is_empty:
            continue
        if not geom.is_valid:
            raise ValueError(f"{label} contains invalid geometry.")
        if geom.geom_type not in ("Polygon", "MultiPolygon"):
            raise ValueError(f"{label} must contain Polygon/MultiPolygon geometry; found {geom.geom_type}.")
        geometries.append(geom)

    if not geometries:
        raise ValueError(f"{label} contains no usable polygon geometry.")

    merged = unary_union(geometries)
    if merged.is_empty:
        raise ValueError(f"{label} geometry is empty.")
    return merged


def normalize_aoi_for_osmium(aoi_path, output_path):
    """Write the AOI as a single GeoJSON Feature, which Osmium extract -p accepts."""
    _, aoi_features = _load_features(aoi_path)
    aoi_geom = _polygon_union(aoi_features, "Project Boundary")

    normalized = {
        "type": "Feature",
        "properties": {},
        "geometry": mapping(aoi_geom),
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(normalized, f)

    return output_path


def validate_geojson_inputs(aoi_path, tasks_path):
    checks = []

    for label, path in (("Project Boundary", aoi_path), ("Task Grid", tasks_path)):
        ok = bool(path and os.path.isfile(path) and os.access(path, os.R_OK))
        checks.append({"ok": ok, "message": f"{label} file is readable." if ok else f"{label} file is missing or unreadable."})

    if not all(c["ok"] for c in checks):
        return {"ok": False, "checks": checks}

    try:
        _, aoi_features = _load_features(aoi_path)
        aoi_geom = _polygon_union(aoi_features, "Project Boundary")
        checks.append({"ok": True, "message": "Project Boundary is valid polygon GeoJSON."})
    except Exception as exc:
        checks.append({"ok": False, "message": f"Project Boundary is invalid: {exc}"})
        return {"ok": False, "checks": checks}

    try:
        _, task_features = _load_features(tasks_path)
        task_geom = _polygon_union(task_features, "Task Grid")
        checks.append({"ok": True, "message": f"Task Grid is valid polygon GeoJSON ({len(task_features)} features)."})
    except Exception as exc:
        checks.append({"ok": False, "message": f"Task Grid is invalid: {exc}"})
        return {"ok": False, "checks": checks}

    overlap = aoi_geom.intersects(task_geom)
    checks.append({"ok": overlap, "message": "Task Grid intersects the Project Boundary." if overlap else "Task Grid does not intersect the Project Boundary."})
    return {"ok": all(c["ok"] for c in checks), "checks": checks}


def validate_pbf(pbf_path):
    if not pbf_path or not os.path.isfile(pbf_path) or not os.access(pbf_path, os.R_OK):
        return {"ok": False, "message": "Geofabrik PBF file is missing or unreadable."}

    result = subprocess.run(["osmium", "fileinfo", "-e", pbf_path], capture_output=True, text=True)
    if result.returncode == 0:
        return {"ok": True, "message": "Geofabrik PBF is readable by Osmium."}

    detail = (result.stderr or result.stdout or "unknown Osmium error").strip()
    return {"ok": False, "message": f"Geofabrik PBF could not be read by Osmium: {detail}"}


def validate_inputs(aoi_path, tasks_path, pbf_path=None, check_pbf=False):
    result = validate_geojson_inputs(aoi_path, tasks_path)
    if not result["ok"]:
        return result

    if check_pbf:
        pbf_result = validate_pbf(pbf_path)
        result["checks"].append(pbf_result)
        result["ok"] = result["ok"] and pbf_result["ok"]

    return result
