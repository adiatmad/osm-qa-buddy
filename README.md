# OSM QA Buddy

**A third-pass quality-assurance helper for HOT Tasking Manager projects.**

> QA Buddy identifies OSM features and tasks that deserve attention. A human mapper makes the decision.

OSM QA Buddy takes an existing OSM extract and a HOT Task Grid, prepares the data for JOSM validation, and turns the saved validation findings into task-level QA outputs.

The recommended workflow uses the normal **JOSM desktop Validator**. QA Buddy handles data preparation, reading JOSM's native XML export, filtering findings to the project's QA scope, associating findings with task cells, and producing reports.

**QA Buddy does not fix OSM data, replace JOSM, or decide whether a finding is valid.**

---

## Choose your workflow

| Workflow | Best for | Entry point |
|---|---|---|
| **JOSM GUI Validation Bridge** (recommended) | Mappers and project teams who want to run the normal JOSM Validator and review findings themselves | Double-click `Launch_OSM_QA_Buddy.vbs` |
| Legacy native/headless pipeline | Existing automated runs, regression checks, and development | `run_qa.bat` |

Use the GUI bridge unless you specifically need the legacy automated pipeline. The two workflows have different setup requirements; the GUI bootstrap does not prepare the legacy Java/JOSM/Jython toolchain.

## How the recommended workflow works

```text
OSM PBF extract + HOT Task Grid GeoJSON
                  |
                  v
       QA Buddy checks the inputs
                  |
                  v
       Osmium clips the OSM data
       to the Task Grid geometry
                  |
                  v
              sample.osm
                  |
                  v
       Open in your installed JOSM
                  |
                  v
       Run the normal JOSM Validator
       Review findings; save the
       "Validation errors" layer as XML
                  |
                  v
          QA Buddy finalizes
                  |
                  v
       Parse native JOSM XML
       Apply QA-scope filter
       Match findings to task cells
       Generate GeoJSON, report, map
```

**JOSM is the validation engine.** QA Buddy does not duplicate JOSM's validation rules or silently run a second validator in the GUI workflow.

---

## Requirements

### Recommended GUI workflow

- Windows 10/11.
- An internet connection for the first launch and dependency setup.
- A writable folder containing this repository.
- **JOSM already installed** and configured to open `.osm` files.
- An OSM PBF extract covering the project area.
- The HOT Task Grid as GeoJSON.

You do **not** need to install Python, Conda/Miniforge, or Osmium Tool manually for the recommended GUI workflow. The launcher prepares a private runtime for this checkout.

The GUI bootstrap does **not** install Java or JOSM. It uses the Windows file association to open `sample.osm` in your existing JOSM installation.

### Legacy native/headless workflow

The legacy workflow has separate prerequisites:

- Python 3.12 or newer.
- A compatible Java runtime.
- A working Osmium Tool executable.
- The JOSM and Jython components prepared by `setup_native.py`.

The GUI's private `.qabot-runtime\` environment does not install or configure this legacy toolchain.

---

## Install and launch (Windows GUI)

1. Download the repository as a ZIP and extract it, or clone it with Git.
2. Keep the extracted repository in a folder where your Windows account can write files.
3. Double-click **`Launch_OSM_QA_Buddy.vbs`**.
4. On first launch, the visible PowerShell setup downloads the official Miniforge installer, checks its SHA-256 digest, creates a private Python 3.12 environment, installs the required packages and Osmium Tool, verifies the runtime, and starts the GUI.
5. On later launches, the bootstrap checks the existing runtime, repairs missing dependencies when possible, and starts the GUI.

The runtime is stored inside this checkout at `.qabot-runtime\`. It does not register a global Python installation, modify Windows PATH permanently, or require administrator privileges. Keep the repository folder in place; the launcher and runtime live there.

First launch needs internet access and several hundred MB of free disk space. If setup fails, read the visible PowerShell error, fix the underlying issue, and run the VBS launcher again. Do not delete your run-output folders to repair the runtime.

You do not need Git after downloading a ZIP. Git is only needed to clone the repository or pull future updates.

---

## Run a QA check

### 1. Prepare the sample

In the GUI's **Prepare** tab:

1. Select the regional **OSM PBF** file (`.osm.pbf`).
2. Select the HOT **Task Grid GeoJSON** file.
3. Click **Start QA Run**.

QA Buddy performs input checks, extracts the OSM data using the union of the Task Grid geometries, and creates a run folder under `gui_runs\` with a timestamp. When preparation completes, the GUI shows the path to `sample.osm` and moves to the JOSM validation step.

For this workflow, the Task Grid is the extraction geometry. A separate project-boundary file is not required.

### 2. Validate in JOSM

1. In the GUI's **Validate in JOSM** tab, click **Open sample.osm in JOSM**.
2. If Windows does not open JOSM, associate `.osm` files with your installed JOSM and try again.
3. In JOSM, run Validator with **Shift+V**. Run it without a selection if you intend to validate the whole prepared sample.
4. Review the Validation errors layer in JOSM.
5. Select the **Validation errors** layer and use **File → Save As** to export it as XML.

Save the XML wherever convenient. Its filename does not need to be `validation_errors.xml`; QA Buddy asks you to select the file in the next step.

**Important:** JOSM's Validator window shows the findings produced by your normal JOSM configuration. QA Buddy applies its own project-scope filter after reading the XML. Do not assume the JOSM window itself has already been filtered by QA Buddy.

### 3. Finalize in QA Buddy

1. Return to the GUI and open the **Finalize** tab.
2. Select the XML file exported from JOSM.
3. Click **Finalize QA Run**.
4. When processing finishes, use **Open Report** and **Open Map** if those outputs are available.

QA Buddy parses the native JOSM XML, filters findings to the supported QA scope, associates finding locations with Task Grid cells, and generates task-level outputs.

The GUI remembers the latest run's Task Grid, sample, and output folder in a small local session file. Keep the input files and repository run folder available until finalization is complete.

---

## What findings are included?

JOSM runs its normal validator configuration. QA Buddy then applies a thematic filter to the exported findings:

- Findings affecting OSM objects tagged `building=*`.
- Findings affecting OSM objects tagged `highway=*`.
- Generic **TagChecker** findings.
- **DuplicateNode** findings.

Address-validation findings are excluded. Other unrelated feature families are excluded unless they fall into one of the explicitly retained generic categories.

For generic geometry/topology checks, QA Buddy uses the affected OSM primitives in the prepared sample to determine whether a finding concerns a building or highway. It does not rely only on the validator's rule name.

This filter controls what appears in QA Buddy's final findings and task summary. It does not change JOSM's validator rules or preferences.

---

## Understand the outputs

Each GUI run is stored in its own timestamped folder under `gui_runs\`. The GUI displays the active folder.

| Output | Purpose |
|---|---|
| `task_grid_qa_summary.geojson` | Original Task Grid with QA counts, rule summaries, task status, and `qa_priority` added to task properties |
| `qa_errors.geojson` | Filtered JOSM findings as GeoJSON |
| `report.html` | Human-readable QA report |
| `map.html` | Interactive map of QA findings and task results |
| `validation_errors.xml` | Copy of the XML exported from JOSM |
| `sample.osm` | OSM dataset prepared for JOSM validation |
| `sample.osm.ready.json` | Preparation hand-off metadata; not an OSM file |
| `run_metadata.json` | Run inputs, validation mode/status, and processing metadata |

The most useful output for project coordination is usually **`task_grid_qa_summary.geojson`**. It lets a team inspect QA signals by task instead of treating the whole project as one undifferentiated result.

### What does `qa_priority` mean?

It is a sorting aid, **not an AI score, a quality grade, or proof that a task is wrong**.

| Priority | Current rule |
|---|---|
| **HIGH** | Task is marked `BADIMAGERY`, or has at least 5 unique findings, or at least 5 unique OSM objects |
| **MEDIUM** | At least 2 unique findings, or at least 2 unique OSM objects, without a HIGH condition |
| **LOW** | At least one finding, without a HIGH or MEDIUM condition |
| **NONE** | No finding signal and task is not marked BADIMAGERY |

Always inspect the actual findings and the OSM context before contacting a mapper or changing data. A finding can be a false positive, a data issue outside the mapper's control, or something that needs local knowledge.

### Unassigned findings

Findings are assigned to tasks when their reported location is covered by a Task Grid polygon. Findings that do not fall inside any task polygon are preserved as unassigned rather than being forced into a task. This can happen near task boundaries or outside the grid.

---

## Optional: send review candidates to BetterWorkspace

QA Buddy includes an optional exporter for a separate JOSM-compatible review layer. It is intended for use with BetterWorkspace's existing multi-validation workflow; it is not required for normal QA Buddy reporting.

Run this from the repository folder after a GUI run has produced `qa_errors.geojson`. Use the private Python runtime created by the launcher:

```cmd
".qabot-runtime\env\python.exe" betterworkspace_export.py "gui_runs\YOUR_RUN\qa_errors.geojson" "gui_runs\YOUR_RUN\sample.osm" "gui_runs\YOUR_RUN\betterworkspace_candidates.osm" --task-grid "C:\data\task_grid.geojson"
```

Replace `YOUR_RUN` and the task-grid path with the actual paths on your computer.

The exporter creates:

- `betterworkspace_candidates.osm`: candidate **ways** and their referenced nodes, copied from the prepared source dataset.
- `betterworkspace_candidates.json`: sidecar manifest with finding details, provenance, and task IDs when recoverable.

The first interoperability milestone is **way-first**: node-only and relation-only findings remain in the normal QA Buddy outputs but are not exported as BetterWorkspace candidates. QA metadata is kept in the JSON manifest, not injected into OSM tags. Open the candidate layer in JOSM and use BetterWorkspace's existing workflow to add the ways to Todo. A human mapper must review each candidate.

The exporter does not depend on BetterWorkspace internals, does not upload or edit OSM data, and does not automatically mark anything as fixed.

---

## Legacy native/headless workflow

The older automated pipeline remains available for existing users and regression/development work. Start it from Windows Command Prompt:

```cmd
run_qa.bat
```

This launcher checks for Python 3.12+, runs `setup_native.py`, and starts the older GUI/application path. The native setup prepares the JOSM tested JAR and (unless `--gui-only` is used) Jython 2.7.3. Java and a working Osmium Tool must be available.

This is a separate architecture from the recommended GUI Validation Bridge:

- The **GUI bridge** asks the user to run JOSM Validator and save its Validation errors XML.
- The **legacy pipeline** runs its automated JOSM/Jython validation path and downloads its configured HOT and third-pass rule sources.

Do not use the GUI bootstrap as evidence that the legacy prerequisites are installed.

---

## Troubleshooting

### The first-launch setup does not complete

Read the PowerShell window's error. Check internet access, free disk space, and whether your network or security software blocks GitHub or conda-forge downloads. Then run the VBS launcher again.

If Miniforge itself is visibly incomplete, close QA Buddy and remove only `.qabot-runtime\miniforge\` before retrying. Do not delete the whole repository or `gui_runs\`.

### Osmium Tool is not detected

The GUI bootstrap installs the actual `osmium.exe` command-line tool in the private runtime. The Python package named `osmium` (pyosmium) is not a replacement for the Osmium Tool executable.

### JOSM does not open `sample.osm`

Check the Windows file association for `.osm` files and point it to your installed JOSM. Open `sample.osm`, not `sample.osm.ready.json`; the latter is only a metadata hand-off marker.

### I cannot find the JOSM XML file during finalization

In JOSM, select the **Validation errors** layer and save that layer as XML. Then select the exact saved file in QA Buddy's Finalize tab. The XML can have any filename and can be stored outside the run folder.

### Finalization fails

The GUI reports the pipeline exit code and recent log lines. Read those diagnostics first and inspect the active timestamped run folder under `gui_runs\`. If a report or map was generated before a later failure, its button remains enabled as long as the corresponding HTML file exists.

### The Report or Map button is disabled

The button is enabled only when its corresponding `report.html` or `map.html` file exists in the active run folder. Check the finalization log and folder contents.

### There are many findings

A large finding count is not automatically a failed run or proof of poor mapping. Review the finding types, affected OSM objects, and local context.

### Some findings are unassigned

This is expected when a finding location is outside all task polygons. QA Buddy preserves these findings rather than guessing a task assignment.

---

## More documentation

- [JOSM GUI Validation Bridge details](docs/josm-gui-validation-bridge.md)

---

## Project status and principles

OSM QA Buddy is an unofficial tool under active development.

- JOSM remains the validation authority in the recommended GUI workflow.
- QA Buddy reports evidence; it does not make mapping decisions.
- Task attribution is geometric and may leave findings unassigned.
- BetterWorkspace export is an optional review hand-off, not an edit or upload mechanism.
- Outputs should be reviewed by people familiar with the project and local mapping context.

> Keep the workflow reproducible, the outputs inspectable, and the human decision-maker in control.

## AI-assisted development

AI tools have supported parts of the project's design, implementation, documentation, and maintenance. The human maintainer remains responsible for reviewing, validating, and approving code changes and QA outputs.
