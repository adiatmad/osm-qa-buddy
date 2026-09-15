"""Keep JOSM findings relevant to buildings and highways.

JOSM remains the validation engine. This module does not recreate JOSM
validation rules; it only classifies the native exported finding text so QA
Buddy can highlight the requested themes.
"""

from __future__ import annotations

import re

# Generic JOSM validation categories the user explicitly wants retained.
_ALWAYS_KEEP_RULES = {"TagChecker", "DuplicateNode"}

# JOSM class/analyser titles and messages commonly used for building checks,
# including HOT Tasking Manager MapCSS rules and the legacy oversize rule.
_BUILDING_TERMS = (
    "building",
    "right angle building",
    "overlapping building",
    "unclosed building",
    "building area",
    "building size",
)

# Prefer explicit highway terminology. "way" alone is deliberately excluded:
# many JOSM geometry tests operate on ways that are not highways.
_HIGHWAY_TERMS = (
    "highway",
    "road",
    "motorway",
    "trunk road",
    "primary road",
    "secondary road",
    "tertiary road",
    "residential road",
    "service road",
    "living street",
    "street",
    "footway",
    "cycleway",
    "path",
    "pedestrian",
    "bridleway",
    "steps",
    "track",
)

# Address validation is explicitly excluded even when its affected object is
# a building or highway.
_ADDRESS_TERMS = ("address", "addresses", "addr:")


def _normalise(*values: str | None) -> str:
    return " ".join(value.strip().lower() for value in values if value).strip()


def _contains_term(text: str, terms: tuple[str, ...]) -> bool:
    for term in terms:
        if re.search(rf"(?<![a-z0-9]){re.escape(term)}(?![a-z0-9])", text):
            return True
    return False


def is_target_josm_finding(finding: dict) -> bool:
    """Return True for building/highway findings plus requested generic rules.

    The native XML parser supplies the analyser name, class title, and message.
    Classification is intentionally based on the actual JOSM finding text,
    rather than duplicating JOSM's internal validator class hierarchy.
    """
    analyser = str(finding.get("analyser", finding.get("rule", "")))
    class_title = str(finding.get("rule_detail", ""))
    message = str(finding.get("message", ""))

    if analyser in _ALWAYS_KEEP_RULES:
        return True

    text = _normalise(analyser, class_title, message)
    if _contains_term(text, _ADDRESS_TERMS):
        return False

    return _contains_term(text, _BUILDING_TERMS) or _contains_term(text, _HIGHWAY_TERMS)


def filter_josm_findings(findings: list[dict]) -> tuple[list[dict], int]:
    """Return target findings and the number removed from the native export."""
    kept = [finding for finding in findings if is_target_josm_finding(finding)]
    return kept, len(findings) - len(kept)
