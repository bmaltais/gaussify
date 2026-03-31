import zipfile
import tarfile
from pathlib import Path
from gaussify.downloader import pick_asset, is_installed, mark_installed, _common_root


def test_pick_asset_matches_substrings():
    assets = [
        {"name": "ffmpeg-n8.1-win64-gpl.zip", "size": 1000},
        {"name": "ffmpeg-n8.1-linux64-gpl.tar.xz", "size": 1000},
        {"name": "ffmpeg-n8.1-win64-gpl.zip.sha256", "size": 100},
    ]
    result = pick_asset(assets, "win64-gpl", ".zip")
    assert result["name"] == "ffmpeg-n8.1-win64-gpl.zip"


def test_pick_asset_excludes_sha256():
    assets = [{"name": "tool.zip.sha256", "size": 50}]
    assert pick_asset(assets, "tool.zip") is None


def test_pick_asset_no_match():
    assets = [{"name": "tool-linux.tar.xz", "size": 1000}]
    assert pick_asset(assets, "win64") is None


def test_is_installed_false_when_missing(tmp_path):
    assert is_installed(tmp_path, "ffmpeg") is False


def test_mark_and_is_installed(tmp_path):
    mark_installed(tmp_path, "ffmpeg", "v1.0")
    assert is_installed(tmp_path, "ffmpeg") is True
    assert (tmp_path / "ffmpeg" / ".installed").read_text() == "v1.0"


def test_common_root_detected():
    names = ["myapp/bin/tool", "myapp/lib/foo", "myapp/README"]
    assert _common_root(names) == "myapp/"


def test_common_root_no_root():
    names = ["bin/tool", "lib/foo"]
    assert _common_root(names) == ""


def test_extract_zip(tmp_path):
    from gaussify.downloader import extract
    archive = tmp_path / "test.zip"
    dest = tmp_path / "out"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("myapp/bin/tool.exe", b"binary")
        zf.writestr("myapp/README", b"readme")
    extract(archive, dest, strip_root=True)
    assert (dest / "bin" / "tool.exe").exists()
    assert (dest / "README").exists()
