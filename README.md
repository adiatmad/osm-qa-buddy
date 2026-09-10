# OSM QA Buddy

**An unofficial companion for HOT Tasking Manager projects, built to support third-pass QA.**

OSM QA Buddy helps a HOT Tasking Manager Project Manager answer one simple question:

> **“After normal validation is finished, where should my validators look again?”**

It runs established JOSM validation rules against completed project data, connects potential issues to Tasking Manager tasks, and highlights areas that deserve human review.

**QA Buddy detects. The PM decides.**

---

## Before you start — one critical prerequisite

**The HOT Tasking Manager project should already be completed and 100% validated.**

QA Buddy is a **third-pass** check. It is not intended to replace the normal mapping and validation workflow.

The basic workflow is:

```text
Mapping
   ↓
Normal validation
   ↓
100% validated project
   ↓
OSM QA Buddy
   ↓
Priority areas / tasks
   ↓
Human review
```

This has currently been tested end-to-end on **Windows with Docker**. Mac and Linux users are welcome to try it and report their results so we can improve cross-platform support.

---

## The PM workflow

The intended workflow is deliberately simple.

### 1. Start QA Buddy

On Windows, run:

```text
run_qa.bat
```

### 2. Enter the HOT TM Project ID

For example:

```text
63564
```

QA Buddy uses this ID to open the official Tasking Manager download links.

### 3. Download the project boundary

Click **HOT TM Project Boundary**.

Your browser opens the official Tasking Manager download link. Download the file yourself.

### 4. Download the task grid

Click **HOT TM Task Grid** and download the file yourself.

### 5. Download the OSM data

Click **Geofabrik Downloads**.

Choose the appropriate country or region and download the matching `.osm.pbf` file.

### 6. Select the three files

Choose the files you downloaded:

| File | Expected filename |
|---|---|
| Project Boundary | ends with `-aoi.geojson` |
| Task Grid | ends with `-tasks.geojson` |
| Geofabrik data | ends with `.osm.pbf` |

Windows duplicate filenames such as `(1)` are accepted.

### 7. Start the third-pass validation

Click:

**START 3RD PASS VALIDATION**

QA Buddy checks the files, prepares the OSM data, and runs JOSM validation inside Docker.

### 8. Use the result

The main output for a PM is:

**`task_grid_qa_summary.geojson`**

Open it in your usual GIS/map workflow and use it to identify **priority tasks or areas for validators to review**.

That's the main idea. **You do not need to understand every technical finding to use the result.**

---

## What problem does it solve?

A HOT Tasking Manager project can reach **100% validated** and still contain quality issues that are easy to miss.

A PM normally does not want to inspect every task again. QA Buddy provides an additional automated signal that helps the PM focus the next round of human review.

It is **not an official HOT Tasking Manager product** and it **does not replace human validation**.

---

## What does “third-pass QA” mean?

QA Buddy is not another mapping editor and it is not a replacement for validators.

It is an additional automated check after the normal Tasking Manager workflow.

For example, QA Buddy may identify:

- suspicious tagging
- duplicated nodes
- crossing ways
- untagged or empty ways
- other issues detected by JOSM validation rules
- tasks marked **BADIMAGERY** by Tasking Manager

These are **potential issues**, not automatic proof that the mapping is wrong.

A human still makes the final decision.

---

## The result you actually care about

### `task_grid_qa_summary.geojson`

This is the file a PM is most likely to use.

It keeps the Tasking Manager task grid and adds QA information to each task, such as:

- `taskId`
- `taskStatus`
- number of QA findings
- number of unique findings
- number of affected OSM objects
- error/warning counts
- validation rules involved
- BADIMAGERY status
- QA priority

The goal is simple:

> **Find the tasks that deserve attention first.**

The PM does not need to reconcile raw JOSM findings or understand the internal processing to use this output.

### Other outputs

| File | Purpose |
|---|---|
| `report.html` | Human-readable QA summary and audit information |
| `map.html` | Interactive map of tasks and findings |
| `qa_errors.geojson` | Raw JOSM findings used as the authoritative QA output |
| `task_grid_qa_summary.geojson` | Task-level QA result for PM use |
| `sample.osm` | OSM data clipped to the project area |
| `qa_run.log` | Full Docker/JOSM processing log |

---

## What happens behind the scenes?

You do **not** need to understand this part to use the tool.

```text
HOT TM Project ID
        ↓
Download links opened for you
        ↓
You select the downloaded files
        ↓
File checks
        ↓
Docker pre-flight checks
        ↓
Osmium clips OSM data to the project area
        ↓
JOSM + Jython run validation rules
        ↓
Findings are connected to Tasking Manager tasks
        ↓
Task-level QA GeoJSON
        ↓
Map + report + audit information
```

The important design principle is **no silent failure**: if the input data does not look right or the QA pipeline cannot run, the process should stop and tell you rather than quietly producing a misleading result.

---

## Where does the data come from?

QA Buddy intentionally **does not automatically download the source data**.

You choose the exact files that will be audited. This makes the run easier to reproduce and gives the PM a clear record of what was checked.

### Official Tasking Manager sources

**Project Boundary**

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/queries/aoi/?as_file=true
```

**Task Grid**

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/tasks/?as_file=true
```

### OSM data

**Geofabrik Downloads**

```text
https://download.geofabrik.de/
```

---

## Safety checks before QA

Before JOSM validation starts, QA Buddy checks that:

- the selected files exist and can be read
- the Project Boundary is valid polygon data
- the Task Grid is valid polygon data
- the Task Grid overlaps the Project Boundary
- the Geofabrik PBF can be read by Osmium

If these checks fail, QA stops before producing a QA result.

---

## Requirements

You need:

- Python 3 with Tkinter
- Docker Desktop
- Internet access for the manual source downloads and JOSM/HOT validation rules

**Current platform status:** end-to-end testing has been completed on Windows with Docker. Mac and Linux users are welcome to try the workflow and report results so cross-platform support can be improved.

You **do not** need to install these locally:

- Java
- JOSM
- Jython
- Shapely
- Osmium

Docker provides them for the QA run.

---

## Why Docker?

QA Buddy uses Docker so that the important QA components run in a controlled environment instead of depending on every user's local Java, JOSM, Python, and Osmium setup.

In simple terms:

> **Docker helps make the QA environment consistent from one computer to another.**

---

## Trust and limitations

QA Buddy is designed to provide evidence, not false certainty.

It does **not** claim:

- that every OSM error will be detected
- that every JOSM warning is actually a mapping mistake
- that a task with no findings is automatically perfect
- that automated QA can replace a human validator

Instead:

> **QA Buddy detects → the PM reviews the evidence → validators make the final decision.**

The tool also keeps raw findings, logs, input information, and derived task-level results so that a QA run can be inspected later.

---

## Example: HOT TM Project 63564

A real Windows end-to-end run was completed successfully for HOT TM Project **63564**.

The run processed:

- **60 task features**
- a readable Geofabrik PBF
- AOI clipping with Osmium
- JOSM/Jython validation
- **78 raw JOSM findings**
- task-level QA summaries
- the HTML report and interactive map

The run demonstrated why task-level output is useful: the raw JOSM findings are technical details, while the PM primarily needs to know **where to focus human review**.

---

## Development status

The project includes automated checks for:

- Python syntax
- QA aggregation and task-priority logic
- report/map generation
- Docker image building
- machine-aware JVM RAM policy

This is an **unofficial tool under active development**. Real-world testing and skeptical review are encouraged.

If something looks wrong, please treat the result as a signal to investigate—not as an unquestionable answer.
