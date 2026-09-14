# OSM QA Buddy

**An unofficial companion for HOT Tasking Manager projects, built for third-pass QA.**

> **QA Buddy detects. The PM decides.**

OSM QA Buddy runs established JOSM validation rules against already-completed HOT Tasking Manager project data, associates findings with tasks, and produces an explainable task-level triage layer for human review.

---

## What it is for

The expected workflow is:

```text
Mapping
  ↓
Normal validation
  ↓
100% validated HOT TM project
  ↓
OSM QA Buddy
  ↓
Task-level QA signals
  ↓
Human review
```

It is a **third-pass QA instrument**, not a replacement for mapping or human validation.

---

## Current workflow: native Windows

The current PM workflow is native Windows. Docker remains in the repository only as a future Tech Team packaging option.

```text
run_qa.bat
  ↓
Python GUI
  ↓
Optional HOT TM Project ID
  ↓
Select Boundary + Task Grid + Geofabrik PBF
  ↓
Preflight validation
  ↓
Native Osmium extraction
  ↓
JOSM 19613 + Jython 2.7.3
  ↓
Task-level GeoJSON + HTML report
```

### Requirements

- Windows
- Python 3.12+ with Tkinter
- 64-bit Java available as `java` on PATH
- Osmium available as `osmium` on PATH
- Git
- No Docker required

Check the host:

```powershell
python --version
java -version
osmium --version
git --version
```

---

## Quick start

Clone once:

```powershell
git clone https://github.com/adiatmad/osm-qa-buddy.git
cd osm-qa-buddy
```

Then launch:

```powershell
.\run_qa.bat
```

`run_qa.bat` selects Python 3.12+, runs native prerequisite setup, downloads the pinned JOSM/Jython runtimes when needed, and opens the GUI.

Pinned QA components:

- JOSM tested revision: **19613**
- Jython: **2.7.3**

---

## GUI workflow

### 1. Project ID — optional

A numeric HOT TM Project ID is useful because QA Buddy can construct the official AOI and Task Grid download links.

**It is not required to run QA.** If you already have the three source files, leave the Project ID blank.

This is intentional: the QA engine should validate the **contents of the selected files**, not depend on filenames or require a HOT TM project ID when the data is already available.

### 2. Select the three source files

Select:

1. **Project Boundary** — HOT TM AOI GeoJSON
2. **Task Grid** — HOT TM task GeoJSON
3. **Geofabrik PBF** — matching country/regional `.osm.pbf`

**Filename patterns are not required.** `nepal-aoi.geojson`, `my_boundary.geojson`, `tasks_final.geojson`, or Windows duplicate names such as `(1)` are all acceptable if their contents are valid.

Preflight validates the actual data before JOSM starts.

### 3. Choose Java/JOSM RAM

Example:

```text
Java/JOSM RAM (GB): 24
```

This is passed directly to Java as `-Xmx`. Do not allocate more RAM than the machine can spare.

### 4. Start validation

Click:

**START 3RD PASS VALIDATION**

The GUI displays the native pipeline log live.

---

## What happens during a run

1. Validate the selected files.
2. Normalize the project boundary for Osmium extraction.
3. Clip the regional PBF with native Osmium.
4. Prepare HOT TM MapCSS rules with Python 3.
5. Run JOSM 19613 through Jython 2.7.3.
6. Aggregate findings against Tasking Manager task polygons.
7. Generate GeoJSON, HTML, map, and technical metadata.

If preflight fails, QA stops instead of silently producing a misleading result.

Each run records input filenames, file sizes, SHA-256 hashes, Java/JOSM/Jython/Osmium versions, and extracted-dataset information in `run_metadata.json`.

---

## Primary outputs

### `task_grid_qa_summary.geojson`

The main PM-facing output. It keeps the Tasking Manager task grid and adds fields such as:

- `taskId`
- `taskStatus`
- `qa_finding_count`
- `qa_unique_finding_count`
- `qa_unique_osm_object_count`
- `qa_error_count`
- `qa_warning_count`
- `qa_rules_involved`
- `qa_badimagery`
- `qa_priority`

Use it to answer:

> **Which tasks deserve human attention first?**

### `report.html`

The human-readable QA summary, including overall findings, duplicate information, task-level results, BADIMAGERY information, and run details.

### Supporting outputs

| File | Purpose |
|---|---|
| `map.html` | Interactive map |
| `qa_errors.geojson` | Raw JOSM findings |
| `sample.osm` | Osmium-clipped OSM dataset |
| `qa_run.log` | Full native processing log |
| `run_metadata.json` | Reproducibility/toolchain metadata |

---

## Interpreting the result

Findings are **signals for human review**, not proof that mapping is wrong.

A task with no findings is also not proof that it is perfect.

> **QA Buddy detects → PM reviews the evidence → validators make the final decision.**

### `qa_priority`

This is an explainable triage signal, not an AI quality score:

- **HIGH** — BADIMAGERY, or at least 5 unique findings, or 5+ unique OSM objects
- **MEDIUM** — 2–4 unique findings or 2–4 unique OSM objects
- **LOW** — one finding without a HIGH/MEDIUM signal
- **NONE** — no QA finding signal and not BADIMAGERY

---

## Verified large-area baseline

A real native Windows run completed successfully on **2026-09-14** with:

- Boundary: `nepal-aoi.geojson`
- Task Grid: `tasks_nepal-tasks.geojson`
- PBF: `nepal-260913.osm.pbf`
- Java/JOSM heap: 24 GB
- Osmium: 1.19.1
- JOSM: 19613
- Jython: 2.7.3

Osmium produced:

- **226,902 nodes**
- **27,848 ways**
- **140 relations**
- **254,890 total OSM objects**

JOSM loaded **260,816 objects** and completed validation in approximately **31 minutes**.

The dominant validator was `Ways` / CrossingWays:

```text
Ways: 1853.88 seconds (~30.9 minutes)
```

The completed run produced:

- **856 raw JOSM findings**
- **747 task-associated findings**
- **109 unassigned findings**
- **1 BADIMAGERY task**

This is a **reproducibility baseline, not a performance guarantee**. CrossingWays is a full-dataset spatial test and runtime depends heavily on the geometry and density of the extracted OSM data.

Long periods without new JOSM validator output are therefore not automatically a hang. The native orchestrator emits a 30-second heartbeat while JOSM is still running.

---

## Data sources

### HOT Tasking Manager

Boundary:

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/queries/aoi/?as_file=true
```

Task Grid:

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/tasks/?as_file=true
```

### Geofabrik

```text
https://download.geofabrik.de/
```

### HOT TM MapCSS rules

```text
https://josm.openstreetmap.de/josmfile?page=Rules/ValidatingBuildingsInHOTTMProjects&zip=1
```

Rules are downloaded with Python 3 before Jython/JOSM starts because older Jython HTTPS support can fail on some systems.

---

## Reproducibility notes

The QA-side Java components are pinned:

| Component | Version |
|---|---|
| JOSM tested revision | `19613` |
| Jython | `2.7.3` |
| Java heap | Selected in GUI |
| Osmium | Native host installation |

`setup_native.py` downloads and SHA-256 verifies the JOSM JAR. Runtime JARs are intentionally not committed to Git.

For a reproducible test, keep the same:

- Boundary data
- Task Grid data
- PBF snapshot
- Osmium version
- JOSM/Jython versions
- Java heap

The run metadata records these inputs and versions so a slow or suspicious result can be investigated instead of guessed at.

---

## Development methodology

Coding work on this repository follows a proportional **Spec Kit + Anti-Slop** approach:

- **Spec Kit**: specify the problem → plan → implement → converge.
- **Anti-Slop**: evidence before claims, minimal necessary complexity, intentional changes, and no cargo-cult engineering.
- **Performance/debugging**: reproduce and measure before making speculative optimizations.

The goal is not process for its own sake. The goal is to make the smallest change that solves the real problem and can be reproduced by another person.

---

## Docker status

Docker is **not part of the current PM workflow**. Docker-related files remain for future Tech Team packaging.

For current testing:

> **Use the native Windows workflow.**

---

## Development status

OSM QA Buddy is an **unofficial tool under active development**.

Treat QA output as evidence to investigate, not as an unquestionable answer.
