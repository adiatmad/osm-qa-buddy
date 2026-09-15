# Third-pass validator sources

OSM QA Buddy loads these external JOSM MapCSS rule sources in addition to its existing built-in and HOT TM rules.

| Source | Role | Current source/version noted upstream |
|---|---|---|
| https://raw.githubusercontent.com/MissingMaps/3rdPassJOSMRules/refs/heads/main/MM_3rdPassValidationRules.mapcss | Missing Maps 3rd Pass rules | `Missing Maps 3rd Pass Validation Rules`, version `1` (source file modified 2026-06-18) |
| https://josm.openstreetmap.de/josmfile?page=Rules/ValidatingBuildingsInHOTTMProjects&zip=1 | HOT TM Validator Checker | `31_2026-03-21` |
| https://josm.openstreetmap.de/josmfile?page=Rules/QAToolInspiredValidations&zip=1 | QA Tool Inspired Validations | `37_2020-11-06` |

The HOT TM Validator Checker was already part of QA Buddy before this change, so it is not downloaded twice.

The pipeline caches the downloaded rule sources under the run work directory. This keeps repeated runs fast while still allowing a fresh work directory to reproduce the current upstream rules.
