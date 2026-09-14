from pathlib import Path


def test_native_runner_shape():
    app = Path("app.py").read_text(encoding="utf-8")
    orchestrator = Path("orchestrator.py").read_text(encoding="utf-8")
    preflight = Path("preflight.py").read_text(encoding="utf-8")
    setup = Path("setup_native.py").read_text(encoding="utf-8")
    bot = Path("bot.py").read_text(encoding="utf-8")
    assert "_native_worker" in app
    assert "--ram-gb" in app
    assert "--project-id" in app
    assert "sample.osm.ready.json" in app
    assert "Project Boundary" not in app
    assert "docker" not in app.lower()
    assert "normalize_task_grid_for_osmium" in preflight
    assert "union_of_task_grid" in orchestrator
    assert "sample.osm.ready.json" in orchestrator
    assert "org.python.util.jython" in orchestrator
    assert "os.pathsep" in orchestrator
    assert 'JOSM_VERSION = "19613"' in orchestrator
    assert 'JYTHON_VERSION = "2.7.3"' in orchestrator
    assert "--project-id" in orchestrator
    assert "project_id=project_id" in orchestrator
    assert "sha256" in orchestrator
    assert "JOSM_SHA256" in setup
    assert "find_mapcss_files" in bot
    assert "hot_rules_dir" in bot
    assert "external_rules_dir" in bot
    assert "should_keep_error" in bot
    assert "Processing objects " not in bot
    assert "batch_size = 10000" not in bot


if __name__ == "__main__":
    test_native_runner_shape()
    print("Native smoke checks passed.")
