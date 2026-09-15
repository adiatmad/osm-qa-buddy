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
 Save Validation errors.xml
        ↓
   QA Buddy finalizes
        ↓
Task-level QA results + map + report
```

**JOSM does the validation. QA Buddy does the preparation, task matching, and reporting.**

---

## What you need

This workflow currently targets **Windows**.

Install these first:

- **Python 3.12+**
- **Java 64-bit**
- **Osmium**
- **Git**
- **JOSM**

You do **not** need Docker.

Check that Windows can find the command-line tools:

```cmd
python --version
java -version
osmium --version
git --version
```

If these commands work, you are ready to start.

---

# Quick start: JOSM GUI Validation Bridge

## 1. Download QA Buddy

Open Command Prompt (`cmd.exe`) and run:

```cmd
git clone https://github.com/adiatmad/osm-qa-buddy.git
cd osm-qa-buddy
```

If you already cloned it, just enter the folder:

```cmd
cd C:\path\to\osm-qa-buddy
```

---

## 2. Get your two input files

You need:

1. **OSM PBF** — the regional/country `.osm.pbf` containing the area you want to check.
2. **Task Grid GeoJSON** — the HOT Tasking Manager task grid for the project.

You do **not** need to rename the files.

For example:

```text
C:\data\nepal.osm.pbf
C:\data\tasks_nepal-tasks.geojson
```

The project boundary is not a separate input for this bridge command; QA Buddy uses the task grid to prepare the run.

---

## 3. Prepare the JOSM dataset

Run:

```cmd
python -u gui_pipeline.py prepare "C:\data\nepal.osm.pbf" "C:\data\tasks_nepal-tasks.geojson" "C:\data\qa-result"
```

Replace the three paths with your own files/folder.

When it finishes, QA Buddy will tell you where `sample.osm` was created.

### Important

**Open `sample.osm` in JOSM.**

Do **not** open:

```text
sample.osm.ready.json
```

The `.ready.json` file is only a small metadata/handoff file. It is not OSM data.

---

## 4. Run normal JOSM validation

Open `sample.osm` in **normal JOSM**.

Then:

1. Let JOSM finish loading the data.
2. Make sure nothing is selected if you want to validate the whole dataset.
3. Press **Shift+V** to run the JOSM Validator.
4. Review the validation results.
5. Select the **Validation errors** layer.
6. Use **File → Save As**.
7. Save it as an XML file, for example:

```text
C:\data\qa-result\validation_errors.xml
```

That's the only manual JOSM step QA Buddy needs.

---

## 5. Give the JOSM results back to QA Buddy

Back in Command Prompt, run:

```cmd
python -u gui_pipeline.py finalize "C:\data\tasks_nepal-tasks.geojson" "C:\data\qa-result\validation_errors.xml" "C:\data\qa-result"
```

Replace the paths with your own.

If everything is OK, you will see:

```text
[+] GUI PIPELINE SUCCEEDED
```

Done. 🎉

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

### `python` is not recognized

Install Python 3.12+ and make sure Python is available on PATH.

### `osmium` is not recognized

Install Osmium and make sure `osmium` works from Command Prompt.

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

Check that JOSM actually saved the **Validation errors** layer as XML and that the path in your `finalize` command points to that file.

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
