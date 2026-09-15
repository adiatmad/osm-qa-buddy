"""Parse JOSM's native Validation errors XML export.

JOSM owns validation. QA Buddy only translates the native export into the
existing point-based GeoJSON finding shape used by task/grid attribution.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path


_LEVEL_TO_SEVERITY = {
    "1": "ERROR",
    "2": "WARNING",
    "3": "OTHER",
}


def _local_name(tag: str) -> str:
    """Return an XML tag name without a namespace, if one is present."""
    return tag.rsplit("}", 1)[-1]


def _text_value(element: ET.Element, attribute: str, default: str = "") -> str:
    value = element.get(attribute)
    return value.strip() if value else default


def _primitive_id(element: ET.Element) -> str | None:
    kind = _local_name(element.tag)
    if kind not in {"node", "way", "relation"}:
        return None
    object_id = element.get("id")
    if not object_id:
        return None
    return f"{kind}/{object_id}"


def _class_map(analyser: ET.Element) -> dict[str, dict[str, str]]:
    classes: dict[str, dict[str, str]] = {}
    for element in analyser:
        if _local_name(element.tag) != "class":
            continue
        class_id = element.get("id")
        if not class_id:
            continue
        level = element.get("level", "")
        title = ""
        for child in element:
            if _local_name(child.tag) == "classtext":
                title = _text_value(child, "title")
                if title:
                    break
        classes[class_id] = {
            "severity": _LEVEL_TO_SEVERITY.get(level, f"LEVEL_{level or 'UNKNOWN'}"),
            "rule": title or f"JOSM class {class_id}",
        }
    return classes


def parse_josm_validation_xml(path: str | Path) -> list[dict]:
    """Parse a JOSM ``Validation errors`` XML export.

    Returns one normalized finding per ``<error>`` element. All affected OSM
    primitives embedded by JOSM are retained in ``object_ids`` while
    ``object_id`` preserves the first primitive for compatibility with the
    existing QA Buddy aggregation/ranking code.
    """
    source = Path(path)
    if not source.is_file():
        raise FileNotFoundError(f"JOSM validation XML not found: {source}")

    root = ET.parse(source).getroot()
    if _local_name(root.tag) != "analysers":
        raise ValueError("Not a JOSM Validation errors XML file: root element must be <analysers>")

    findings: list[dict] = []
    for analyser in root:
        if _local_name(analyser.tag) != "analyser":
            continue
        analyser_name = _text_value(analyser, "name", "Unknown")
        classes = _class_map(analyser)

        for error in analyser:
            if _local_name(error.tag) != "error":
                continue
            class_id = error.get("class", "")
            error_class = classes.get(class_id, {})
            severity = error_class.get("severity", "UNKNOWN")
            rule = error_class.get("rule", analyser_name)

            location = None
            message = ""
            object_ids: list[str] = []
            for child in error:
                name = _local_name(child.tag)
                if name == "location":
                    try:
                        lat = float(child.get("lat"))
                        lon = float(child.get("lon"))
                        location = [lon, lat]
                    except (TypeError, ValueError):
                        location = None
                elif name in {"node", "way", "relation"}:
                    object_id = _primitive_id(child)
                    if object_id and object_id not in object_ids:
                        object_ids.append(object_id)
                elif name == "text":
                    message = _text_value(child, "value")

            if not location:
                # JOSM normally writes a location for every TestError. Do not
                # fabricate coordinates if a malformed/foreign file omits it.
                continue
            if not object_ids:
                # Existing QA Buddy ranking is object-based; an error without
                # an affected primitive cannot be attributed safely.
                continue

            findings.append(
                {
                    "severity": severity,
                    "rule": rule,
                    "message": message,
                    "object_id": object_ids[0],
                    "object_ids": object_ids,
                    "coordinates": location,
                    "analyser": analyser_name,
                    "class_id": class_id,
                }
            )

    return findings


def write_geojson(findings: list[dict], output_path: str | Path) -> Path:
    """Write normalized findings using QA Buddy's existing GeoJSON shape."""
    import json

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    features = []
    for finding in findings:
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": finding["coordinates"]},
                "properties": {
                    "rule": finding["rule"],
                    "message": finding["message"],
                    "severity": finding["severity"],
                    "object_id": finding["object_id"],
                    "object_ids": finding["object_ids"],
                    "analyser": finding["analyser"],
                    "class_id": finding["class_id"],
                },
            }
        )
    output.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2), encoding="utf-8")
    return output
