from pathlib import Path


def test_native_runner_shape():
    app = Path("app.py").read_text(encoding="utf-8")
    orchestrator = Path("orchestrator.py").read_text(encoding="utf-8")
    setup = Path("setup_native.py").read_text(encoding="utf-8")
    assert "_native_worker" in app
    assert "--ram-gb" in app
    assert "docker" not in app.lower()
    assert "org.python.util.jython" in orchestrator
    assert "os.pathsep" in orchestrator
    assert "JOSM_VERSION = \"19613\"" in orchestrator
    assert "JYTHON_VERSION = \"2.7.3\"" in orchestrator
    assert "JOSM_SHA256" in setup


if __name__ == "__main__":
    test_native_runner_shape()
    print("Native smoke checks passed.")
