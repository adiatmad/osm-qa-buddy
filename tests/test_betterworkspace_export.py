from pathlib import Path

from betterworkspace_export import export_review_candidates


def test_export_review_candidates_preserves_candidate_way_and_nodes(tmp_path: Path):
    findings = tmp_path / "qa_errors.geojson"
    findings.write_text(
        """{
          "type": "FeatureCollection",
          "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [125.8, -8.5]},
            "properties": {
              "object_id": "way/10",
              "object_ids": ["way/10"],
              "rule": "TestRule",
              "rule_detail": "Test detail",
              "message": "Review this way",
              "severity": "WARNING"
            }
          }]
        }""",
        encoding="utf-8",
    )
    source = tmp_path / "sample.osm"
    source.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<osm version="0.6" generator="test">
  <node id="1" lat="-8.5" lon="125.8"><tag k="name" v="A"/></node>
  <node id="2" lat="-8.5" lon="125.81"/>
  <node id="3" lat="-8.51" lon="125.81"/>
  <way id="10">
    <nd ref="1"/>
    <nd ref="2"/>
    <nd ref="3"/>
    <tag k="highway" v="residential"/>
  </way>
  <way id="20"><nd ref="2"/><nd ref="3"/></way>
</osm>
""",
        encoding="utf-8",
    )
    output = tmp_path / "candidates.osm"
    manifest = tmp_path / "candidates.json"

    export_review_candidates(findings, source, output, manifest)

    text = output.read_text(encoding="utf-8")
    assert 'way id="10"' in text
    assert 'way id="20"' not in text
    assert 'node id="1"' in text
    assert 'node id="2"' in text
    assert 'node id="3"' in text
    assert 'k="highway" v="residential"' in text
    assert "qabot" not in text

    manifest_text = manifest.read_text(encoding="utf-8")
    assert '"object_id": "way/10"' in manifest_text
    assert '"human_review_required": true' in manifest_text


def test_export_review_candidates_includes_task_attribution(tmp_path: Path):
    findings = tmp_path / "qa_errors.geojson"
    findings.write_text(
        """{
          "type": "FeatureCollection",
          "features": [{
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [125.8, -8.5]},
            "properties": {"object_id": "way/10", "object_ids": ["way/10"]}
          }]
        }""",
        encoding="utf-8",
    )
    source = tmp_path / "sample.osm"
    source.write_text(
        """<osm version="0.6">
  <node id="1" lat="-8.5" lon="125.8"/>
  <node id="2" lat="-8.5" lon="125.81"/>
  <way id="10"><nd ref="1"/><nd ref="2"/></way>
</osm>""",
        encoding="utf-8",
    )
    task_grid = tmp_path / "tasks.geojson"
    task_grid.write_text(
        """{
          "type": "FeatureCollection",
          "features": [{
            "type": "Feature",
            "geometry": {
              "type": "Polygon",
              "coordinates": [[[125.79, -8.51], [125.82, -8.51], [125.82, -8.49], [125.79, -8.49], [125.79, -8.51]]]
            },
            "properties": {"taskId": 123}
          }]
        }""",
        encoding="utf-8",
    )

    output = tmp_path / "candidates.osm"
    manifest = tmp_path / "candidates.json"
    export_review_candidates(findings, source, output, manifest, task_grid)

    manifest_text = manifest.read_text(encoding="utf-8")
    assert '"task_ids": [' in manifest_text
    assert "123" in manifest_text
