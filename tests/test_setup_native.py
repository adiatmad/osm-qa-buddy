from zipfile import ZipFile

from setup_native import is_valid_josm_jar


def test_accepts_a_jar_containing_josm_main_application(tmp_path):
    jar = tmp_path / "josm-tested.jar"
    with ZipFile(jar, "w") as archive:
        archive.writestr("org/openstreetmap/josm/gui/MainApplication.class", b"class")

    assert is_valid_josm_jar(jar)


def test_rejects_non_jar_download(tmp_path):
    download = tmp_path / "josm-tested.jar"
    download.write_text("404 Not Found", encoding="utf-8")

    assert not is_valid_josm_jar(download)


def test_rejects_zip_without_josm_application(tmp_path):
    jar = tmp_path / "not-josm.jar"
    with ZipFile(jar, "w") as archive:
        archive.writestr("README.txt", "not JOSM")

    assert not is_valid_josm_jar(jar)
