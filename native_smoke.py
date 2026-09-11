from pathlib import Path


def test_native_runner_shape():
    app = Path("app.py").read_text(encoding="utf-8")
    orchestrator = Path("orchestrator.py").read_text(encoding="utf-8")
    setup = Path("setup_native.py").read_text(encoding="utf-8")
    bot = Path("bot.py").read_text(encoding="utf-8")
    assert "_native_worker" in app
    assert "--ram-gb" in app
    assert "docker" not in app.lower()
    assert "org.python.util.jython" in orchestrator
    assert "os.pathsep" in orchestrator
    assert "JOSM_VERSION = \"19613\"" in orchestrator
    assert "JYTHON_VERSION = \"2.7.3\"" in orchestrator
    assert "JOSM_SHA256" in setup
    assert "os.listdir(extract_path)" in bot
    assert "for root, dirs, files in os.walk(extract_path)" in bot
    assert "Processing objects " not in bot
    assert "batch_size = 10000" not in bot


if __name__ == "__main__":
    test_native_runner_shape()
    print("Native smoke checks passed.")
