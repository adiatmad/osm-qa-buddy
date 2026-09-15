"""Keep JOSM findings relevant to buildings and highways.

JOSM remains the validation engine. This module does not recreate JOSM
validation rules; it classifies native exported findings using the affected
OSM primitives when the prepared sample is available, with a text fallback
for explicitly named JOSM/HOT rules.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from pathlib import Path

_ALWAYS_KEEP_RULES = {"TagChecker", "DuplicateNode"}
_BUILDING_TERMS = ("building", "right angle building", "overlapping building", "unclosed building", "building area", "building size")
_HIGHWAY_TERMS = (
    "highway", "road", "motorway", "trunk road", "primary road", "secondary road",
    "tertiary road", "residential road", "service road", "living street", "street",
    "footway", "cycleway", "path", "pedestrian", "bridleway", "steps", "track",
)
_ADDRESS_TERMS = ("address", "addresses", "addr:")


def _normalise(*values: str | None) -> str:
    return " ".join(value.strip().lower() for value in values if value).strip()


def _contains_term(text: str, terms: tuple[str, ...]) -> bool:
    return any(re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text) for term in terms)


def load_osm_feature_tags(osm_path: str | Path) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    """Load tags and relation members from the prepared OSM XML sample."""
    tags: dict[str, dict[str, str]] = {}
    members: dict[str, list[str]] = {}
    path = Path(osm_path)
    if not path.is_file():
        raise FileNotFoundError(f"OSM sample not found: {path}")

    for event, element in ET.iterparse(path, events=("end",)):
        kind = element.tag.rsplit("}", 1)[-1]
        if kind not in {"node", "way", "relation"}:
            continue
        object_id = element.get("id")
        if not object_id:
            element.clear()
            continue
        key = f"{kind}/{object_id}"
        tags[key] = {
            child.get("k", ""): child.get("v", "")
            for child in element
            if child.tag.rsplit("}", 1)[-1] == "tag" and child.get("k")
        }
        if kind == "relation":
            members[key] = [
                f"{member.get('type')}/{member.get('ref')}"
                for member in element
                if member.tag.rsplit("}", 1)[-1] == "member"
                and member.get("type") and member.get("ref")
            ]
        element.clear()
    return tags, members


def _object_has_theme(object_id: str, theme: str, tags: dict[str, dict[str, str]], members: dict[str, list[str]], seen: set[str] | None = None) -> bool:
    seen = seen or set()
    if object_id in seen:
        return False
    seen.add(object_id)
    object_tags = tags.get(object_id, {})
    if theme == "building" and "building" in object_tags:
        return True
    if theme == "highway" and "highway" in object_tags:
        return True
    return any(_object_has_theme(member, theme, tags, members, seen) for member in members.get(object_id, []))


def is_target_josm_finding(
    finding: dict,
    tags: dict[str, dict[str, str]] | None = None,
    members: dict[str, list[str]] | None = None,
) -> bool:
    """Return True for building/highway findings plus requested generic rules."""
    analyser = str(finding.get("analyser", finding.get("rule", "")))
    class_title = str(finding.get("rule_detail", ""))
    message = str(finding.get("message", ""))

    if analyser in _ALWAYS_KEEP_RULES:
        return True

    text = _normalise(analyser, class_title, message)
    if _contains_term(text, _ADDRESS_TERMS):
        return False

    if tags is not None:
        members = members or {}
        object_ids = finding.get("object_ids") or ([finding["object_id"]] if finding.get("object_id") else [])
        if any(_object_has_theme(object_id, "building", tags, members) for object_id in object_ids):
            return True
        if any(_object_has_theme(object_id, "highway", tags, members) for object_id in object_ids):
            return True

    # Explicitly named building/highway rules, including HOT MapCSS and the
    # custom oversize-building rule, remain useful even without an OSM sample.
    return _contains_term(text, _BUILDING_TERMS) or _contains_term(text, _HIGHWAY_TERMS)


def filter_josm_findings(
    findings: list[dict],
    osm_path: str | Path | None = None,
) -> tuple[list[dict], int]:
    """Return target findings and the number removed from the native export."""
    tags = members = None
    if osm_path:
        tags, members = load_osm_feature_tags(osm_path)
    kept = [finding for finding in findings if is_target_josm_finding(finding, tags, members)]
    return kept, len(findings) - len(kept)
