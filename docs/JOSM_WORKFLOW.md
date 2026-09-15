# JOSM-ready dataset workflow

QA Buddy prepares a timestamped OSM dataset for interactive validation in JOSM after the native extraction/QA pipeline completes.

## Artifact

The generated file is named like:

`osm_qa_buddy_josm_20260914_072312.osm`

It is copied from the extracted project dataset after QA finishes. The original working file remains under the run's `work/` directory.

## Why `.osm`?

The project-sized `.osm` file preserves OSM nodes, ways, and relations and can be opened directly by JOSM. JOSM supports opening OSM files directly and also accepts filenames as command-line arguments. This keeps QA Buddy focused on preparing the correct dataset while JOSM remains the interactive validation/editing environment.

## GUI workflow

1. Run the normal native QA workflow.
2. Wait for `QA COMPLETED SUCCESSFULLY`.
3. Use **Open in JOSM** to launch JOSM with the timestamped dataset.
4. Run JOSM's normal Validation workflow and inspect/fix findings there.
5. Use **Open Results Folder** when the raw artifact, report, log, or metadata are needed.

The timestamped filename is intentional: it makes the artifact distinguishable from JOSM tutorials/examples that commonly use `sample.osm`, and makes it easier to correlate the file with a QA run.

## Design boundary

QA Buddy prepares the project-sized dataset and performs its own reproducible automated checks. JOSM remains the interactive source of truth for human validation and editing. QA Buddy does not attempt to automate mouse/keyboard interaction with the JOSM GUI.
