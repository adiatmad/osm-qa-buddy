# Native validation runner experiment

This branch changes two runtime details for the headless QA path:

- JOSM runs on Java 21 instead of Java 17. JOSM recommends Java 21 or later.
- `bot.py` uses JOSM's `ValidationTask` execution path, matching the path used by JOSM's headless `ValidatorCLI`, while preserving QA Buddy's selected validator list and output format.

If the native task cannot run headlessly, the bot falls back to the previous manual validator lifecycle.
