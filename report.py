import json
from collections import Counter
from html import escape
from pathlib import Path

LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
TILES = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"


def _load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _bounds(geometry, current=None):
    if current is None:
        current = [float("inf"), float("inf"), float("-inf"), float("-inf")]
    coords = geometry.get("coordinates", [])
    stack = [coords]
    while stack:
        value = stack.pop()
        if value and isinstance(value[0], (int, float)):
            current[0] = min(current[0], value[0]); current[1] = min(current[1], value[1])
            current[2] = max(current[2], value[0]); current[3] = max(current[3], value[1])
        else:
            stack.extend(value)
    return current


def _center(*feature_collections):
    bounds = None
    for collection in feature_collections:
        for feature in collection.get("features", []):
            geom = feature.get("geometry")
            if geom:
                bounds = _bounds(geom, bounds)
    if not bounds or bounds[0] == float("inf"):
        return [0, 0], 2
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]
    span = max(bounds[2] - bounds[0], bounds[3] - bounds[1])
    zoom = 17 if span < 0.02 else 14 if span < 0.1 else 11 if span < 1 else 8 if span < 5 else 5
    return center, zoom


def _write_map(errors, tasks, output_path):
    center, zoom = _center(errors, tasks)
    html = f'''<!doctype html>
<html><head><meta charset="utf-8"><title>OSM QA Buddy Map</title>
<link rel="stylesheet" href="{LEAFLET_CSS}">
<style>html,body,#map{{height:100%;margin:0}} .legend{{background:white;padding:8px 10px;font:14px sans-serif;line-height:20px;box-shadow:0 1px 5px rgba(0,0,0,.3)}} .swatch{{display:inline-block;width:12px;height:12px;margin-right:5px;border:1px solid #666}}</style>
</head><body><div id="map"></div>
<script src="{LEAFLET_JS}"></script>
<script>
const errors = {json.dumps(errors, ensure_ascii=False)};
const tasks = {json.dumps(tasks, ensure_ascii=False)};
const map = L.map('map').setView({json.dumps(center)}, {zoom});
L.tileLayer('{TILES}', {{maxZoom: 19, attribution: '&copy; OpenStreetMap contributors'}}).addTo(map);
function taskStyle(feature) {{
  const p = feature.properties || {{}};
  const status = String(p.qa_task_status || p.taskStatus || '').toUpperCase();
  if (status === 'BADIMAGERY') return {{color:'#6a1b9a', weight:2, fillOpacity:0.55, fillColor:'#ab47bc'}};
  const n = Number(p.qa_total_issues || 0);
  return {{color:'#333', weight:1, fillOpacity:0.45, fillColor:n===0?'#2ca25f':n<5?'#fee08b':n<10?'#fdae61':'#d73027'}};
}}
const taskLayer = L.geoJSON(tasks, {{
  style: taskStyle,
  onEachFeature: (feature, layer) => {{
    const p = feature.properties || {{}};
    const id = p.taskId ?? p.task_id ?? p.id ?? p.uuid ?? 'Unknown';
    const status = String(p.qa_task_status || p.taskStatus || 'UNKNOWN').toUpperCase();
    const findings = Number(p.qa_finding_count || p.qa_total_issues || 0);
    const objects = Number(p.qa_unique_osm_object_count || 0);
    const rules = Array.isArray(p.qa_rules_involved) ? p.qa_rules_involved.join(', ') : (p.qa_rules_involved || 'None');
    const statusNote = status === 'BADIMAGERY' ? '<br><b>Action:</b> Please review the imagery and confirm whether the task can reasonably be mapped.' : '';
    layer.bindPopup('<b>Task:</b> '+id+'<br><b>Status:</b> '+escapeHtml(status)+'<br><b>Findings:</b> '+findings+'<br><b>Unique OSM objects:</b> '+objects+'<br><b>Rules:</b> '+escapeHtml(rules)+'<br><b>Errors:</b> '+(p.qa_error_count||0)+'<br><b>Warnings:</b> '+(p.qa_warning_count||0)+statusNote);
  }}
}}).addTo(map);
const errorLayer = L.geoJSON(errors, {{
  pointToLayer: (feature, latlng) => L.circleMarker(latlng, {{radius:6, color: ['ERROR','Errors'].includes(feature.properties?.severity)?'#d73027':'#fdae61', fillOpacity:0.8}}),
  onEachFeature: (feature, layer) => {{
    const p = feature.properties || {{}};
    const link = p.josm_remote_url ? '<br><a href="'+p.josm_remote_url+'">Open in JOSM</a>' : '';
    layer.bindPopup('<b>'+escapeHtml(p.rule||'QA issue')+'</b><br>'+escapeHtml(p.message||'')+'<br><b>Severity:</b> '+escapeHtml(p.severity||'')+link);
  }}
}}).addTo(map);
function escapeHtml(value) {{ const d=document.createElement('div'); d.textContent=value; return d.innerHTML; }}
const legend = L.control({{position:'topright'}});
legend.onAdd = function() {{ const div=L.DomUtil.create('div','legend'); div.innerHTML='<b>Task status / findings</b><br><span class="swatch" style="background:#ab47bc"></span>BADIMAGERY<br><span class="swatch" style="background:#2ca25f"></span>0 findings<br><span class="swatch" style="background:#fee08b"></span>1–4<br><span class="swatch" style="background:#fdae61"></span>5–9<br><span class="swatch" style="background:#d73027"></span>10+'; return div; }};
legend.addTo(map);
L.control.layers(null, {{'Task grid': taskLayer, 'QA findings': errorLayer}}).addTo(map);
if (taskLayer.getBounds().isValid()) map.fitBounds(taskLayer.getBounds(), {{padding:[20,20]}});
</script></body></html>'''
    Path(output_path).write_text(html, encoding="utf-8")


def _normalize_severity(value):
    value = str(value or "UNKNOWN").upper()
    if value in {"ERROR", "ERRORS"}:
        return "ERROR"
    if value in {"WARNING", "WARN", "WARNINGS"}:
        return "WARNING"
    return value


def generate_report(errors_path, tasks_path, report_path, map_path, metadata_path=None):
    errors = _load(errors_path); tasks = _load(tasks_path)
    metadata = _load(metadata_path) if metadata_path and Path(metadata_path).exists() else {}
    error_features = errors.get("features", []); task_features = tasks.get("features", [])
    severity_counts = Counter(
        _normalize_severity(f.get("properties", {}).get("severity", "UNKNOWN"))
        for f in error_features
    )
    rule_counts = Counter(f.get("properties", {}).get("rule", "Unknown") for f in error_features)
    issueful_tasks = sum(1 for f in task_features if (f.get("properties", {}).get("qa_finding_count") or f.get("properties", {}).get("qa_total_issues") or 0) > 0)
    unique_objects = sum((f.get("properties", {}).get("qa_unique_osm_object_count") or 0) for f in task_features)
    badimagery_tasks = [
        f for f in task_features
        if str(f.get("properties", {}).get("qa_task_status") or f.get("properties", {}).get("taskStatus") or "").upper() == "BADIMAGERY"
    ]
    badimagery_count = len(badimagery_tasks)
    badimagery_rows = "\n".join(
        f"<tr><td>{escape(str(f.get('properties', {}).get('taskId') or f.get('properties', {}).get('task_id') or f.get('properties', {}).get('id') or f.get('properties', {}).get('uuid') or 'Unknown'))}</td><td><b>BADIMAGERY</b></td><td>Please review the imagery and confirm whether the task can reasonably be mapped.</td></tr>"
        for f in badimagery_tasks
    )
    rows = "\n".join(f"<tr><td>{escape(rule)}</td><td>{count}</td></tr>" for rule, count in rule_counts.most_common()) or '<tr><td colspan="2">No findings</td></tr>'
    toolchain = metadata.get("toolchain", {})
    inputs = metadata.get("inputs", {})
    input_rows = "".join(
        f"<tr><td>{escape(label.replace('_', ' ').title())}</td><td>{escape(data.get('filename', ''))}</td><td>{data.get('size_bytes', 0):,}</td><td><code>{escape(data.get('sha256', ''))}</code></td></tr>"
        for label, data in inputs.items()
    )
    badimagery_section = f'''<div class="warning"><b>⚠️ {badimagery_count} task{'s' if badimagery_count != 1 else ''} marked BADIMAGERY.</b> This is a Tasking Manager task status, not a JOSM QA finding. Please review the imagery and confirm whether the task can reasonably be mapped.</div>
<h2>BADIMAGERY tasks</h2><table><thead><tr><th>Task</th><th>Status</th><th>Action</th></tr></thead><tbody>{badimagery_rows}</tbody></table>''' if badimagery_count else ''
    report = f'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>OSM QA Buddy Report</title>
<style>body{{font:15px Segoe UI,Arial,sans-serif;max-width:1100px;margin:0 auto;padding:28px;background:#f6f7f9;color:#202124}} h1{{margin-bottom:4px}} .muted{{color:#666}} .cards{{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:20px 0}} .card{{background:white;border-radius:10px;padding:18px;box-shadow:0 1px 4px rgba(0,0,0,.1)}} .value{{font-size:28px;font-weight:700}} table{{width:100%;border-collapse:collapse;background:white}} th,td{{padding:10px;border-bottom:1px solid #ddd;text-align:left;vertical-align:top}} a.button{{display:inline-block;background:#333;color:white;text-decoration:none;padding:10px 14px;border-radius:7px;margin:10px 0}} .note{{background:white;border-left:4px solid #666;padding:12px;margin:16px 0}} .warning{{background:#fff8e1;border-left:4px solid #b7791f;padding:12px;margin:16px 0}} code{{word-break:break-all}}</style>
</head><body><h1>OSM QA Buddy — 3rd Pass Validation</h1><div class="muted">Generated automatically from the JOSM QA results.</div>
<div class="warning"><b>Human review required.</b> QA Buddy identifies potential quality issues for review. A finding is not, by itself, proof that the OSM mapping is incorrect.</div>
<div class="cards"><div class="card"><div class="muted">Tasks</div><div class="value">{len(task_features)}</div></div><div class="card"><div class="muted">Tasks with findings</div><div class="value">{issueful_tasks}</div></div><div class="card"><div class="muted">QA findings</div><div class="value">{len(error_features)}</div></div><div class="card"><div class="muted">BADIMAGERY tasks</div><div class="value">{badimagery_count}</div></div></div>
<p><b>Errors:</b> {severity_counts.get('ERROR',0)} &nbsp; <b>Warnings:</b> {severity_counts.get('WARNING',0)} &nbsp; <b>Other/unknown:</b> {len(error_features) - severity_counts.get('ERROR',0) - severity_counts.get('WARNING',0)}</p>
{badimagery_section}
<div class="note"><b>Run audit information</b><br>QA Buddy: {escape(metadata.get('qa_buddy_version', 'unknown'))}<br>Project ID: {escape(str(metadata.get('project_id') or 'not provided'))}<br>Run started (UTC): {escape(metadata.get('run_started_utc', 'unknown'))}<br>Validation engine: {escape(metadata.get('validation_engine', 'unknown'))}<br>JOSM tested version: {escape(toolchain.get('josm_tested_version', 'unknown'))}<br>Jython: {escape(toolchain.get('jython_version', 'unknown'))}<br>Java: {escape(toolchain.get('java_runtime', 'unknown'))}<br>Osmium: {escape(toolchain.get('osmium_version', 'unknown'))}</div>
<h2>Input files</h2><table><thead><tr><th>Input</th><th>Filename</th><th>Size (bytes)</th><th>SHA-256</th></tr></thead><tbody>{input_rows or '<tr><td colspan="4">Input metadata unavailable</td></tr>'}</tbody></table>
<a class="button" href="map.html" target="_blank">Open interactive map</a><h2>Issues by rule</h2><table><thead><tr><th>Rule</th><th>Findings</th></tr></thead><tbody>{rows}</tbody></table>
<h2>Outputs</h2><p><a href="qa_errors.geojson">Raw QA findings GeoJSON</a><br><a href="task_grid_qa_summary.geojson">Task grid QA summary GeoJSON</a><br><a href="run_metadata.json">Run metadata (JSON)</a></p>
</body></html>'''
    Path(report_path).write_text(report, encoding="utf-8")
    _write_map(errors, tasks, map_path)
