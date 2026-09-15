# JOSM GUI validation bridge

## Purpose

QA Buddy does not reimplement JOSM validation. It prepares the Task Grid clip,
then consumes JOSM's native **Validation errors** XML export.

```text
Task Grid + regional PBF
        |
        v
   Osmium extract
        |
        v
     sample.osm
        |
        v
   normal JOSM GUI
        |
        |  Validate (Shift+V)
        |  Save Validation errors layer as XML
        v
 validation_errors.xml
        |
        v
 QA Buddy XML parser
        |
        v
 qa_errors.geojson
        |
        v
 task_grid_qa_summary.geojson
        |
        v
 report.html / map.html
```

## Why XML

JOSM has a native `ValidatorErrorExporter` for the Validation errors layer.
The exporter writes `TestError` objects using `ValidatorErrorWriter`. The XML
contains the error location, severity class, human-readable text, and the
affected OSM primitives. QA Buddy therefore receives the same findings that
the normal GUI displayed instead of running a second validator implementation.

## Interactive CLI workflow

Prepare the dataset:

```powershell
$env:QABOT_WORK_DIR = "C:\path\to\osm-qa-buddy\work\gui-run"
python gui_pipeline.py prepare "C:\data\region.osm.pbf" "C:\data\task_grid.geojson" "C:\data\qa-result"
```

Open the generated `sample.osm` in normal JOSM. Run Validator with `Shift+V`
with no selection so the whole clipped dataset is checked. Review the findings.
Then select the **Validation errors** layer and use **Save As** to save a
`validation_errors.xml` file.

**Open `sample.osm`, not `sample.osm.ready.json`.** The `.ready.json` file is a
QA Buddy handoff marker containing metadata for the prepared dataset; it is not
an OSM dataset and should not be opened in JOSM.

Finalize the run:

```powershell
python gui_pipeline.py finalize "C:\data\task_grid.geojson" "C:\data\qa-result\validation_errors.xml" "C:\data\qa-result"
```

The final output remains compatible with the existing QA Buddy aggregation:

- `qa_errors.geojson`
- `task_grid_qa_summary.geojson`
- `report.html`
- `map.html`
- `run_metadata.json`
- `validation_errors.xml`

## Important boundary behavior

The clipped dataset is intentionally produced with the existing Osmium
extraction behavior. Do **not** add `--set-bounds` merely for this bridge.
JOSM validation can depend on what it knows about the downloaded area, so
changing the dataset bounds would be a semantic change that needs its own
benchmark.

## Rules

In GUI mode JOSM owns the validator configuration. QA Buddy does not inject
headless validator tests, instantiate JOSM `Test` classes, or duplicate rule
logic. If a project requires specific MapCSS sources, configure those sources
in JOSM before running validation.

The old headless path remains available as a regression/development baseline.
The GUI bridge is the path to use when the validation stage must be performed
through normal JOSM GUI validation and its native XML export.

## Current validation status

**Field-validated.** A real Windows run was completed on 2026-09-15 with the
pinned JOSM 19613 workflow and a real Nepal test dataset. QA Buddy parsed 17,202
raw JOSM findings, associated 15,768 with Task Grid polygons, preserved 1,435
unassigned findings, detected 1 BADIMAGERY task, and generated the established
GeoJSON, report, and map outputs.

This is evidence that the bridge works end-to-end for the tested workflow. It
is not a universal guarantee across every JOSM version, validator configuration,
dataset, or task-grid geometry.
