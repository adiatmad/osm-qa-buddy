# OSM QA Buddy

**An unofficial companion for HOT Tasking Manager projects, built to support third-pass QA.**

OSM QA Buddy helps a HOT Tasking Manager Project Manager answer one simple question:

> **“After normal validation is finished, where should my validators look again?”**

It runs established JOSM validation rules against completed project data, connects potential issues to Tasking Manager tasks, and highlights areas that deserve human review.

**QA Buddy detects. The PM decides.**

---

## What this app is for

The project should already be **completed and 100% validated** in HOT Tasking Manager.

```text
Mapping
   ↓
Normal validation
   ↓
100% validated project
   ↓
OSM QA Buddy
   ↓
Priority tasks / areas
   ↓
Human review
```

QA Buddy is a **third-pass QA instrument**. It does not replace mapping or human validation.

---

## Current workflow: native Windows

The current working target is a **native Windows workflow**, not Docker.

Docker files remain in the repository as a future packaging/Tech Team option, but they are **not required for the PM workflow described here**.

The intended user experience is:

```text
run_qa.bat
    ↓
Python GUI
    ↓
Enter HOT TM Project ID
    ↓
Open official download links
    ↓
Select AOI + Task Grid + Geofabrik PBF
    ↓
Enter Java/JOSM RAM, e.g. 24
    ↓
START 3RD PASS VALIDATION
    ↓
native Osmium
    ↓
JOSM 19613 + Jython 2.7.3
    ↓
Task-level QA GeoJSON + report/map/log
```

---

## PM workflow

### 1. Install the host prerequisites

On Windows, install:

- **Python 3.12+** with Tkinter
- **64-bit Java** available as `java` on PATH
- **Osmium** (`osmium` available on PATH)
- **Git**

You do **not** need Docker for the current workflow.

Check the important commands in PowerShell:

```powershell
python --version
java -version
osmium --version
```

### 2. Clone the repository

```powershell
git clone https://github.com/adiatmad/osm-qa-buddy.git
cd osm-qa-buddy
```

### 3. Launch QA Buddy

```powershell
.\run_qa.bat
```

The launcher checks Python, Java, and Osmium, then downloads the pinned JOSM and Jython files if they are not already present.

The pinned versions are:

- **JOSM tested revision: 19613**
- **Jython: 2.7.3**

You can also run the GUI directly with:

```powershell
python setup_native.py
python app.py
```

### 4. Enter the HOT TM Project ID

For example:

```text
63564
```

The numeric ID is only used to construct the official Tasking Manager download links.

### 5. Download the three source files

QA Buddy intentionally **does not automatically download the project source data**. You choose the exact files that will be audited.

You need:

1. **Project Boundary** — HOT Tasking Manager AOI
2. **Task Grid** — HOT Tasking Manager tasks
3. **OSM data** — a matching country/regional `.osm.pbf` from Geofabrik

Expected filename patterns:

| File | Expected filename |
|---|---|
| Project Boundary | ends with `-aoi.geojson` |
| Task Grid | ends with `-tasks.geojson` |
| Geofabrik data | ends with `.osm.pbf` |

Windows duplicate names such as `(1)` are accepted.

### 6. Choose Java/JOSM RAM

The GUI has a simple numeric field:

```text
Java/JOSM RAM (GB): 24
```

Enter a whole number between **1 and 128**. QA Buddy passes that value directly to Java as `-Xmx`.

For example:

```text
24  →  java -Xmx24g ...
```

This is intentionally simple: **you choose the RAM; QA Buddy does not try to guess it.** Do not allocate more RAM than the computer can spare.

### 7. Start validation

Click:

**START 3RD PASS VALIDATION**

The GUI shows the native processing log live.

The pipeline performs:

1. input preflight
2. Osmium clipping of the regional PBF to the project boundary
3. HOT TM MapCSS rule preparation using Python 3
4. JOSM/Jython validation
5. task-level finding aggregation
6. report/map generation

### 8. Use the result

The main PM output is:

**`task_grid_qa_summary.geojson`**

Open it in your normal GIS/map workflow and use the QA fields to identify **priority tasks or areas for human review**.

---

## Main output

### `task_grid_qa_summary.geojson`

This is the primary PM-facing output.

It keeps the Tasking Manager task grid and adds QA information to each task, including fields such as:

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

The goal is simple:

> **Find the tasks that deserve attention first.**

### Other outputs

| File | Purpose |
|---|---|
| `report.html` | Human-readable QA summary and audit information |
| `map.html` | Interactive map of tasks and findings |
| `qa_errors.geojson` | Raw JOSM findings |
| `task_grid_qa_summary.geojson` | Task-level QA result for PM use |
| `sample.osm` | OSM data clipped to the project area |
| `qa_run.log` | Full native processing log |
| `run_metadata.json` | Toolchain, input, RAM, and run metadata |

---

## What the QA result means

QA Buddy can identify signals such as:

- suspicious tagging
- duplicated nodes
- crossing ways
- untagged or empty ways
- other issues detected by JOSM validation rules
- tasks marked **BADIMAGERY** by Tasking Manager

These are **potential issues**, not automatic proof that the mapping is wrong.

A task with no findings is also **not proof that the task is perfect**.

The rule is:

> **QA Buddy detects → the PM reviews the evidence → validators make the final decision.**

---

## Priority field

`qa_priority` is an explainable triage signal, not an AI quality score.

- **HIGH** — BADIMAGERY, or at least 5 unique findings, or at least 5 unique OSM objects
- **MEDIUM** — 2–4 unique findings or 2–4 unique OSM objects
- **LOW** — one finding without a HIGH/MEDIUM signal
- **NONE** — no QA finding signal and not BADIMAGERY

The priority is intended to help a PM decide **where to look first**, not to replace human judgment.

---

## Data sources

### HOT Tasking Manager

Project Boundary:

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

### HOT TM validation rules

During a run, Python 3 downloads the HOT Tasking Manager MapCSS rules before Jython/JOSM starts:

```text
https://josm.openstreetmap.de/josmfile?page=Rules/ValidatingBuildingsInHOTTMProjects&zip=1
```

This is deliberate: the older Jython 2.7 HTTPS stack previously caused failures on some computers. External rule preparation therefore happens in normal Python 3.

---

## Native toolchain

QA Buddy pins the QA-side Java components for reproducibility:

| Component | Version |
|---|---|
| JOSM tested revision | `19613` |
| Jython | `2.7.3` |
| Java heap | selected by user in GUI |
| Osmium | native host installation |

`setup_native.py` downloads the pinned JOSM and Jython JARs into the local `tools/` directory. They are not committed to Git because they are binary dependencies.

---

## Safety checks

Before JOSM validation starts, QA Buddy checks that:

- the selected files exist and can be read
- the Project Boundary is valid polygon data
- the Task Grid is valid polygon data
- the Task Grid overlaps the Project Boundary
- the Geofabrik PBF can be read by Osmium
- the HOT TM MapCSS rules were successfully prepared
- the pinned JOSM/Jython files are available
- Java and Osmium are available on PATH

If these checks fail, QA stops instead of quietly producing a misleading result.

---

## Example: HOT TM Project 63564

A real Windows run of the QA pipeline has been completed for HOT TM Project **63564** using the JOSM/Jython validator stack.

The run demonstrated the intended PM workflow: raw JOSM findings are technical details, while the PM primarily needs to know **where to focus human review**.

---

## Docker status

Docker is **not part of the current PM workflow**.

The repository still contains Docker-related files because the longer-term goal is to let the Tech Team package and standardize the environment later.

For now, the practical message is:

> **If you want to test QA Buddy today, use the native Windows workflow.**

---

## Development status

This is an **unofficial tool under active development**.

The repository includes checks for Python syntax, QA aggregation, priority logic, report/map generation, and other supporting behavior.

Real-world testing and skeptical review are encouraged.

If something looks wrong, treat the result as a signal to investigate—not as an unquestionable answer.
