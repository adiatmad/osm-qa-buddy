# OSM QA Buddy

OSM QA Buddy runs a third-pass validation of a completed HOT Tasking Manager project using JOSM validation rules inside Docker.

## PM workflow

1. Run `run_qa.bat` on Windows.
2. Enter the HOT Tasking Manager Project ID.
3. Open the HOT TM Project Boundary download link and download the file yourself.
4. Open the HOT TM Task Grid download link and download the file yourself.
5. Open **Geofabrik downloads**, choose the appropriate country/region, and download the matching `.osm.pbf` file.
6. Select the three downloaded files in the GUI:
   - Project Boundary: filename ending `-aoi.geojson` (Windows duplicate suffixes such as `(1)` are accepted)
   - Task Grid: filename ending `-tasks.geojson` (Windows duplicate suffixes such as `(1)` are accepted)
   - Geofabrik PBF: filename ending `.osm.pbf` (Windows duplicate suffixes such as `(1)` are accepted)
7. Click **START 3RD PASS VALIDATION**.
8. The app performs local checks, then Docker performs authoritative pre-flight, Osmium clipping, and JOSM/Jython validation.
9. After success, `report.html` opens automatically and `map.html` provides the interactive task/finding map.

The application does not download HOT TM or Geofabrik source data itself. The PM selects the exact source files being audited.

## Official sources

Project Boundary:
`https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/queries/aoi/?as_file=true`

Task Grid:
`https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/tasks/?as_file=true`

Geofabrik:
`https://download.geofabrik.de/`

## Pre-flight

Docker checks that the selected files exist and are readable, both GeoJSON files are valid polygon data, the Task Grid intersects the Project Boundary, and Osmium can read the PBF. Failure stops the pipeline before QA.

## Outputs

Runs create `osm_qa_buddy_results/project_<ID>_<timestamp>/` with:

- `report.html` — PM summary
- `map.html` — interactive task/finding map
- `qa_errors.geojson` — raw JOSM findings, authoritative
- `task_grid_qa_summary.geojson` — derived task metrics
- `sample.osm` — AOI-clipped OSM data
- `qa_run.log` — full Docker/JOSM log

Task metrics include finding count, unique OSM object count, rules involved, error count, warning count, and unknown-severity count.

## Requirements

Windows, Python 3 with Tkinter, Docker Desktop, and internet access for the manual source downloads and JOSM/HOT validation rules.

Java, JOSM, Jython, Shapely, and Osmium do not need to be installed locally; Docker provides them.

## Validation status

A real Windows run of HOT TM Project 63564 completed end-to-end successfully: 60 task features were accepted, the PBF was readable, AOI clipping completed, JOSM/Jython validation ran, 77 raw JOSM findings were produced, and the task summary/report/map were generated.

GitHub Actions CI includes Python syntax checking, a synthetic QA aggregation/report smoke test, and a Docker image build.
