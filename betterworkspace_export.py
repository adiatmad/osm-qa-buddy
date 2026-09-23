"""Export QA Buddy review candidates as a JOSM-compatible OSM layer.

The export is intentionally a plain OSM XML layer. BetterWorkspace can use its
existing multi-validation workflow on the layer without QA Buddy coupling to
BetterWorkspace or Todo plugin internals.

Only ways are exported in the first milestone because BetterWorkspace's
multi-validation workflow operates on JOSM Way primitives. Finding metadata and
task attribution stay in a sidecar manifest rather than being written into OSM
tags.
"""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Iterable


def _primitive_parts(object_id: str) -> tuple[str, int] | None:
    try:
        kind, raw_id = str(object_id).split("/", 1)
        if kind not in {"node", "way", "relation"}:
            return None
        return kind, int(raw_id)
    except (TypeError, ValueError):
        return None


def _load_findings(path: str | Path) -> list[dict]:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError("QA findings must be a GeoJSON FeatureCollection")

    findings: list[dict] = []
    for feature in data.get("features", []):
        properties = feature.get("properties") or {}
        object_ids = properties.get("object_ids") or [properties.get("object_id")]
        valid_ids = [item for item in object_ids if _primitive_parts(item)]
        if not valid_ids:
            continue
        findings.append(
            {
                "object_ids": valid_ids,
                "object_id": properties.get("object_id") or valid_ids[0],
                "rule": properties.get("rule", ""),
                "rule_detail": properties.get("rule_detail", ""),
                "message": properties.get("message", ""),
                "severity": properties.get("severity", ""),
                "coordinates": (feature.get("geometry") or {}).get("coordinates"),
            }
        )
    return findings


def _load_task_grid(path: str | Path) -> list[tuple[str, object]]:
    from shapely.geometry import shape

    data = json.loads(Path(path).read_text(encoding="utf-8"))
    tasks: list[tuple[str, object]] = []
    for feature in data.get("features", []):
        properties = feature.get("properties") or {}
        task_id = properties.get("taskId") or properties.get("task_id") or properties.get("id")
        geometry = feature.get("geometry")
        if task_id is not None and geometry:
            tasks.append((str(task_id), shape(geometry)))
    return tasks


def _task_ids_for_coordinates(coordinates, tasks) -> list[str]:
    if not coordinates or len(coordinates) < 2:
        return []
    from shapely.geometry import Point

    point = Point(float(coordinates[0]), float(coordinates[1]))
    return [task_id for task_id, geometry in tasks if geometry.covers(point)]


def _candidate_way_ids(findings: Iterable[dict]) -> list[int]:
    way_ids: set[int] = set()
    for finding in findings:
        for object_id in finding["object_ids"]:
            parsed = _primitive_parts(object_id)
            if parsed and parsed[0] == "way":
                way_ids.add(parsed[1])
    return sorted(way_ids)


def _parse_root(source: Path) -> ET.Element:
    try:
        return ET.parse(source).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid OSM XML: {source}: {exc}") from exc


def _copy_element(element: ET.Element) -> ET.Element:
    return ET.fromstring(ET.tostring(element, encoding="unicode"))


def export_review_candidates(
    findings_path: str | Path,
    source_osm_path: str | Path,
    output_osm_path: str | Path,
    manifest_path: str | Path | None = None,
    task_grid_path: str | Path | None = None,
) -> tuple[Path, Path]:
    """Export candidate ways and a provenance manifest.

    The source dataset is read twice so referenced nodes can be retained
    without loading the full OSM document into memory. Candidate way tags and
    node tags are copied unchanged; no QA Buddy tags are injected.
    """
    findings = _load_findings(findings_path)
    candidate_ids = set(_candidate_way_ids(findings))
    source = Path(source_osm_path)
    if not source.is_file():
        raise FileNotFoundError(f"Source OSM dataset not found: {source}")

    if not candidate_ids:
        raise ValueError("No candidate ways found in QA findings")

    root = _parse_root(source)
    if root.tag != "osm":
        raise ValueError("Source OSM XML must have an <osm> root")

    ways: dict[int, ET.Element] = {}
    node_ids: set[int] = set()
    for element in root:
        if element.tag != "way":
            continue
        raw_id = element.get("id")
        if raw_id is None:
            continue
        try:
            way_id = int(raw_id)
        except ValueError:
            continue
        if way_id not in candidate_ids:
            continue
        copied = _copy_element(element)
        ways[way_id] = copied
        for child in copied:
            if child.tag == "nd" and child.get("ref"):
                try:
                    node_ids.add(int(child.get("ref")))
                except ValueError:
                    continue

    if not ways:
        raise ValueError("None of the candidate ways were found in the source OSM dataset")

    nodes: dict[int, ET.Element] = {}
    for element in root:
        if element.tag != "node" or not element.get("id"):
            continue
        try:
            node_id = int(element.get("id"))
        except ValueError:
            continue
        if node_id in node_ids:
            nodes[node_id] = _copy_element(element)

    output = Path(output_osm_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    out_root = ET.Element("osm", root.attrib)
    for node_id in sorted(nodes):
        out_root.append(nodes[node_id])
    for way_id in sorted(ways):
        out_root.append(ways[way_id])
    ET.ElementTree(out_root).write(output, encoding="utf-8", xml_declaration=True)

    tasks = _load_task_grid(task_grid_path) if task_grid_path else []
    candidates = []
    for way_id in sorted(ways):
        object_id = f"way/{way_id}"
        matching = [finding for finding in findings if object_id in finding["object_ids"]]
        task_ids = sorted(
            {
                task_id
                for finding in matching
                for task_id in _task_ids_for_coordinates(finding["coordinates"], tasks)
            }
        )
        candidates.append(
            {
                "object_id": object_id,
                "task_ids": task_ids,
                "finding_count": len(matching),
                "findings": [
                    {
                        "rule": finding["rule"],
                        "rule_detail": finding["rule_detail"],
                        "message": finding["message"],
                        "severity": finding["severity"],
                        "coordinates": finding["coordinates"],
                    }
                    for finding in matching
                ],
            }
        )

    manifest = {
        "format": "osm-qa-buddy/betterworkspace-review-candidates/v1",
        "semantics": "review_candidates",
        "source_findings": str(Path(findings_path).name),
        "source_osm": str(source.name),
        "candidate_count": len(candidates),
        "candidate_ways": candidates,
        "human_review_required": True,
        "notes": [
            "Candidate OSM objects are copied unchanged from the source dataset.",
            "QA metadata is kept in this sidecar manifest and is not written into OSM tags.",
            "Load the candidate OSM layer in JOSM and use BetterWorkspace's existing multi-validation workflow to add its ways to Todo.",
        ],
    }
    manifest_output = Path(manifest_path) if manifest_path else output.with_suffix(".json")
    manifest_output.parent.mkdir(parents=True, exist_ok=True)
    manifest_output.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return output, manifest_output


def main() -> None:
    parser = argparse.ArgumentParser(description="Export QA Buddy findings as a BetterWorkspace review layer")
    parser.add_argument("findings", help="QA Buddy qa_errors.geojson")
    parser.add_argument("source_osm", help="JOSM source sample.osm")
    parser.add_argument("output_osm", help="Output candidate OSM layer")
    parser.add_argument("--manifest", default=None, help="Optional output provenance manifest path")
    parser.add_argument("--task-grid", default=None, help="Optional HOT Task Grid GeoJSON for task attribution")
    args = parser.parse_args()
    export_review_candidates(
        args.findings,
        args.source_osm,
        args.output_osm,
        manifest_path=args.manifest,
        task_grid_path=args.task_grid,
    )


if __name__ == "__main__":
    main()
