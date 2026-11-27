# OSM QA Buddy

**A simple third-pass QA helper for HOT Tasking Manager projects.**

> **QA Buddy finds things to look at. A human makes the decision.**

OSM QA Buddy takes an already-mapped HOT Tasking Manager project, finds JOSM validation issues, connects those issues to task-grid cells, and produces a simple list of tasks that may need another look.

It is **not** a replacement for mapping, normal validation, or human review.

---

## The easiest way to use it

If you are new to QA Buddy, use the **JOSM GUI Validation Bridge**.

The idea is deliberately simple:

```text
Your OSM data + Task Grid
        ↓
   QA Buddy prepares
        ↓
     sample.osm
        ↓
   Open in normal JOSM
        ↓
   Run JOSM Validator
        ↓
 Save Validation errors XML
        ↓
   QA Buddy finalizes
        ↓
Task-level QA results + map + report
```

**JOSM does the validation. QA Buddy does the preparation, task matching, and reporting.**

---

## First launch: click the VBS file

You do **not** need to install Python, Java, Osmium Tool, Conda, or JOSM yourself.

1. Download or clone this repository to a folder you can write to.
2. Double-click **Launch_OSM_QA_Buddy.vbs**.
3. On the first launch, a visible setup window downloads and verifies the official Miniforge installer, creates a private Python 3.12 environment, installs Shapely, Osmium Tool and OpenJDK, downloads and verifies the pinned JOSM JAR, then opens the GUI.
4. On later launches, the bootstrap checks the existing runtime, repairs missing dependencies if needed, and opens the GUI.

The runtime is kept in `.qabot-runtime\` inside this checkout. It does not modify your global Python installation or Windows PATH and does not require administrator access. Keep the repository folder in place after setup.

**First launch requires an internet connection and several hundred MB of free disk space.** Downloads are verified before installers/components are used. If setup fails, the PowerShell window stays open with the error; correct the issue and click the VBS again.

You do not need Git after downloading the repository as a ZIP. Git is only needed if you want to clone or update the source.

---

# Quick start: JOSM GUI Validation Bridge

After the GUI opens:

1. Choose your **OSM PBF** file.
2. Choose the **Task Grid GeoJSON** file.
3. Click **Start QA Run**. QA Buddy prepares `sample.osm`.
4. Click **Open sample.osm in JOSM**. QA Buddy launches its prepared JOSM runtime directly; no Windows file association is needed.
5. In JOSM, run Validator with **Shift+V**, review the findings, select the **Validation errors** layer, and use **File → Save As** to save the results as XML.
6. Return to QA Buddy, open the **Finalize** tab, select the XML file, and click **Finalize QA Run**.

QA Buddy then produces the task-level results, map, and report.

The project boundary is not a separate input for this bridge; the Task Grid is the authoritative extraction geometry.

---

# What you get

The most useful file for a project manager is:

### `task_grid_qa_summary.geojson`

This is the task grid with QA information added to each task, including finding counts and a simple `qa_priority`.

It helps answer:

> **Which tasks should I look at first?**

Other useful outputs include:

| File | What it is |
|---|---|
| `task_grid_qa_summary.geojson` | Task-level QA summary |
| `qa_errors.geojson` | JOSM findings as GeoJSON |
| `report.html` | Human-readable report |
| `map.html` | Interactive map |
| `validation_errors.xml` | Native JOSM validation export |
| `sample.osm` | The clipped OSM data checked by JOSM |
| `run_metadata.json` | Information needed to reproduce/debug the run |

---

# What does `qa_priority` mean?

It is **not an AI score** and it does not say that a task is bad.

It is only a simple way to sort tasks for human review:

- **HIGH** — BADIMAGERY or many findings
- **MEDIUM** — several findings
- **LOW** — a small finding signal
- **NONE** — no QA finding signal

Always inspect the actual JOSM findings before deciding what to do.

---

# Why use the JOSM GUI?

QA Buddy deliberately does **not** create its own copy of JOSM's validation rules.

Instead:

- **JOSM** = validation engine
- **QA Buddy** = preparation + parsing + task attribution + reporting

This means the validation result comes from the normal JOSM Validator that mappers already know.

QA Buddy reads JOSM's native **Validation errors XML** after you save it.

---

# A real test

The GUI bridge was tested on Windows with a real Nepal dataset and **JOSM 19613**.

One completed run produced:

- **17,202** raw JOSM findings
- **15,768** task-associated findings
- **1,435** unassigned findings
- **1** BADIMAGERY task

QA Buddy successfully produced the task summary, report, and map.

The unassigned findings are preserved rather than being forced into a task. They can occur when findings fall outside task polygons or involve geometry around task boundaries.

This is real field-validation evidence for the workflow, **not a guarantee that every JOSM version, dataset, or geometry will behave identically**.

---

# Existing native/headless workflow

QA Buddy also has an older automated workflow. It remains useful as a regression/development baseline.

Start it with:

```cmd
run_qa.bat
```

That workflow prepares the data and runs JOSM through its existing automated/headless path.

For new users who want to use the normal JOSM Validator, prefer the **GUI Validation Bridge** described above.

---

# Data sources

QA Buddy can work with data from the usual HOT/OpenStreetMap sources, including:

- HOT Tasking Manager task grids and project boundaries
- Geofabrik `.osm.pbf` extracts
- JOSM validation

You can also use files you already downloaded locally.

---

# Troubleshooting

### First-run setup fails

Read the error in the PowerShell window. Check your internet connection, available disk space, and whether security software or a managed network is blocking GitHub or conda-forge downloads. Then click the VBS launcher again; completed downloads and packages are reused.

The private runtime lives in `.qabot-runtime\`. If that folder contains a clearly incomplete Miniforge installation, close QA Buddy, remove only `.qabot-runtime\miniforge\`, and retry. Do not delete the whole repository or your QA run folders.

### Osmium Tool is not detected

The bootstrap installs and verifies the actual `osmium.exe` command-line tool in the private environment. The Python package named `osmium` (pyosmium) is not a replacement.

### JOSM does not open `sample.osm`

Make sure you opened:

```text
sample.osm
```

not:

```text
sample.osm.ready.json
```

### Finalize says the XML is missing

Check that JOSM actually saved the **Validation errors** layer as XML and that the path in your `finalize` command points to that file. The XML filename and folder can be anything; the path just needs to point to the file you saved.

### There are many findings

That is not automatically a failure. QA Buddy reports what JOSM found. Review the findings before deciding whether anything needs fixing.

### Some findings are unassigned

That is expected in some datasets. QA Buddy keeps them instead of guessing which task they belong to.

---

# More documentation

Detailed GUI bridge documentation:

[`docs/josm-gui-validation-bridge.md`](docs/josm-gui-validation-bridge.md)

The repository also contains the project's Spec Kit and Anti-Slop engineering notes under `specs/`.

---

# Development status

OSM QA Buddy is an **unofficial tool under active development**.

The project follows a simple principle:

> **Keep the tool boring, reproducible, and useful.**

QA output is evidence for human review, not an unquestionable answer.

## AI-Assisted Development

This project was developed and/or maintained with AI assistance. AI was used to support parts of the design, implementation, documentation, and/or maintenance workflow. The human maintainer remains responsible for reviewing, validating, and approving the project's code and outputs.
