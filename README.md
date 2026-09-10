# OSM QA Buddy

**An unofficial companion for HOT Tasking Manager projects, built to support third-pass QA.**

OSM QA Buddy helps a HOT Tasking Manager Project Manager answer one simple question:

> **“After normal validation is finished, where should my validators look again?”**

It runs established JOSM validation rules against completed project data, connects potential issues to Tasking Manager tasks, and highlights areas that deserve human review.

**QA Buddy detects. The PM decides.**

---

## Before you start

**The HOT Tasking Manager project should already be completed and 100% validated.**

QA Buddy is a **third-pass** check. It does not replace normal mapping or validation.

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

The current end-to-end workflow has been tested on **Windows with Docker Desktop and WSL 2**. Mac and Linux users are welcome to try it and report results so cross-platform support can improve.

---

## PM workflow

### 1. Download the project data

QA Buddy intentionally lets you download the source files yourself. You need:

1. **Project Boundary** — from HOT Tasking Manager
2. **Task Grid** — from HOT Tasking Manager
3. **OSM data** — a matching country or regional `.osm.pbf` from Geofabrik

Enter the HOT TM Project ID in QA Buddy and use the download buttons to open the official links/pages.

Expected filenames:

| File | Expected filename |
|---|---|
| Project Boundary | ends with `-aoi.geojson` |
| Task Grid | ends with `-tasks.geojson` |
| Geofabrik data | ends with `.osm.pbf` |

Windows duplicate filenames such as `(1)` are accepted.

### 2. Run QA Buddy

Open **PowerShell**, go to the repository folder, and run:

```powershell
.\run_qa.bat
```

**PowerShell note:** use `.\run_qa.bat`, not `run_qa.bat`.

This builds the Docker image and opens the QA Buddy GUI.

You can also start the GUI directly with:

```powershell
python app.py
```

but `.\run_qa.bat` is the recommended launcher because it builds the Docker image first.

### 3. Enter the HOT TM Project ID

For example:

```text
63564
```

QA Buddy uses the numeric ID to construct the official Tasking Manager download links.

### 4. Select the three downloaded files

Choose the Project Boundary, Task Grid, and Geofabrik PBF.

### 5. Start validation

Click:

**START 3RD PASS VALIDATION**

QA Buddy performs input checks, clips the PBF with Osmium, and runs JOSM validation inside Docker. The GUI shows the live processing log.

The HOT Tasking Manager MapCSS rules are downloaded by the container's **Python 3** runtime before Jython/JOSM validation starts. This avoids relying on the older Jython 2.7 HTTPS stack for external downloads.

### 6. Use the result

The main PM output is:

**`task_grid_qa_summary.geojson`**

Open it in your normal GIS/map workflow and use it to identify **priority tasks or areas for validators to review**.

You do not need to understand every technical JOSM finding to use the main output.

---

## Setting up a new Windows computer

For the current tested workflow, install:

- **Python 3.12**
- **Git**
- **Docker Desktop**
- **WSL 2**

Docker Desktop on Windows uses WSL 2 for the Linux-container workflow.

### One-line WinGet installation

On a new Windows computer, the main software can be installed with:

```powershell
winget install Python.Python.3.12 Git.Git Docker.DockerDesktop Microsoft.WSL --exact
```

WinGet supports multiple package IDs in a single `install` command. The package IDs used here are Python 3.12, Git, Docker Desktop, and Microsoft WSL.

After installation, reboot Windows if requested. Start Docker Desktop and make sure its **WSL 2 based engine/backend** is enabled.

### Verify the prerequisites

Open PowerShell:

```powershell
python --version
wsl --version
docker --version
docker info
```

Expected:

- Python **3.12.x**
- WSL 2 is available
- Docker is installed
- `docker info` successfully returns Docker Desktop information

Then clone and launch QA Buddy:

```powershell
git clone https://github.com/adiatmad/osm-qa-buddy.git
cd osm-qa-buddy
.\run_qa.bat
```

If the Docker image builds successfully and the QA Buddy window opens, the main local prerequisites are working.

### Application-level checks

From the repository folder:

```powershell
python -m py_compile app.py orchestrator.py memory.py preflight.py report.py run_wizard.py test_smoke.py test_memory.py
python test_memory.py
python test_smoke.py
```

These checks verify Python syntax, RAM policy tests, and the existing QA/report smoke tests. The Docker build performed by `.\run_qa.bat` verifies that the container environment can be assembled.

**You do not need to install Java, JOSM, Jython, Shapely, or Osmium on the host computer.** They are provided inside Docker.

---

## What problem does it solve?

A HOT Tasking Manager project can reach **100% validated** and still contain quality issues that are easy to miss.

A PM normally does not want to inspect every task again. QA Buddy provides an additional automated signal so the PM can focus the next round of human review.

It is **not an official HOT Tasking Manager product** and **does not replace human validation**.

---

## What does “third-pass QA” mean?

QA Buddy is an additional automated check after the normal Tasking Manager workflow.

It may identify:

- suspicious tagging
- duplicated nodes
- crossing ways
- untagged or empty ways
- other issues detected by JOSM validation rules
- tasks marked **BADIMAGERY** by Tasking Manager

These are **potential issues**, not automatic proof that the mapping is wrong. A human still makes the final decision.

---

## The result you actually care about

### `task_grid_qa_summary.geojson`

This is the primary PM output.

It keeps the Tasking Manager task grid and adds QA information to each task, including fields such as:

- `taskId`
- `taskStatus`
- QA finding counts
- unique finding counts
- affected OSM object counts
- error/warning counts
- validation rules involved
- BADIMAGERY status
- QA priority

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
| `qa_run.log` | Full Docker/JOSM processing log |
| `run_metadata.json` | Toolchain, input, and run metadata |

---

## What happens behind the scenes?

```text
HOT TM Project ID
        ↓
Official download links opened for you
        ↓
You select the downloaded files
        ↓
Input checks
        ↓
Docker pre-flight checks
        ↓
Osmium clips OSM data to the project area
        ↓
Python 3 downloads HOT TM MapCSS rules
        ↓
JOSM + Jython run validation rules
        ↓
Findings are connected to Tasking Manager tasks
        ↓
Task-level QA GeoJSON
        ↓
Map + report + audit information
```

The important design principle is **no silent failure**: if the input data does not look right or the QA pipeline cannot run, the process should stop and report the problem instead of quietly producing a misleading result.

---

## Where does the data come from?

QA Buddy intentionally **does not automatically download the project source data**. You choose the exact files that will be audited.

### Official Tasking Manager sources

Project Boundary:

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/queries/aoi/?as_file=true
```

Task Grid:

```text
https://tasking-manager-production-api.hotosm.org/api/v2/projects/<PROJECT_ID>/tasks/?as_file=true
```

### OSM data

Geofabrik:

```text
https://download.geofabrik.de/
```

### HOT TM validation rules

During the QA run, the Docker container downloads the HOT Tasking Manager MapCSS rules from:

```text
https://josm.openstreetmap.de/josmfile?page=Rules/ValidatingBuildingsInHOTTMProjects&zip=1
```

The download is handled by Python 3 before Jython/JOSM validation starts.

---

## Safety checks before QA

Before JOSM validation starts, QA Buddy checks that:

- the selected files exist and can be read
- the Project Boundary is valid polygon data
- the Task Grid is valid polygon data
- the Task Grid overlaps the Project Boundary
- the Geofabrik PBF can be read by Osmium
- the HOT TM MapCSS rules were successfully prepared

If these checks fail, QA stops before producing a QA result.

---

## Requirements

For the current supported/tested Windows workflow:

- Windows with **WSL 2**
- **Python 3.12** with Tkinter
- **Docker Desktop** using the WSL 2 backend
- **Git**
- Internet access for the manual source downloads and HOT/JOSM validation rules

**Current platform status:** end-to-end testing has been completed on Windows with Docker Desktop and WSL 2. Mac and Linux users are welcome to try the workflow and report results so cross-platform support can improve.

You **do not** need to install these locally:

- Java
- JOSM
- Jython
- Shapely
- Osmium

Docker provides them for the QA run.

---

## Why Docker?

QA Buddy uses Docker so the important QA components run in a controlled environment instead of depending on every user's local Java, JOSM, Python, and Osmium setup.

On Windows, Docker Desktop uses the **WSL 2 backend** for this Linux-container workflow.

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

The tool keeps raw findings, logs, input information, and derived task-level results so that a QA run can be inspected later.

---

## Example: HOT TM Project 63564

A real Windows end-to-end run was completed for HOT TM Project **63564**.

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

This is an **unofficial tool under active development**. Real-world testing and skeptical review are encouraged.

If something looks wrong, treat the result as a signal to investigate—not as an unquestionable answer.
