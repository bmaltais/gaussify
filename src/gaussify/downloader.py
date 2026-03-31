"""
Shared download + extract utilities for binary installers.
"""
import json
import shutil
import tarfile
import tempfile
import urllib.request
import zipfile
from pathlib import Path

import typer


def get_latest_release(repo: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(url, headers={"User-Agent": "gaussify-installer"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def get_release_by_tag(repo: str, tag: str) -> dict:
    url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
    req = urllib.request.Request(url, headers={"User-Agent": "gaussify-installer"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def pick_asset(assets: list, *substrings: str) -> dict | None:
    for asset in assets:
        name = asset["name"]
        if all(s in name for s in substrings) and not name.endswith(".sha256"):
            return asset
    return None


def download(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "gaussify-installer"})
    with urllib.request.urlopen(req) as r:
        total = int(r.headers.get("Content-Length", 0))
        downloaded = 0
        chunk = 65536
        with open(dest, "wb") as f:
            while True:
                buf = r.read(chunk)
                if not buf:
                    break
                f.write(buf)
                downloaded += len(buf)
                if total:
                    pct = downloaded * 100 // total
                    typer.echo(f"\r  {pct}% ({downloaded // 1024 // 1024} MB)", nl=False)
    typer.echo()


def extract(archive: Path, dest: Path, strip_root: bool = True) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    name = archive.name

    if name.endswith(".zip"):
        with zipfile.ZipFile(archive) as zf:
            _extract_zip(zf, dest, strip_root)
    elif name.endswith((".tar.xz", ".tar.gz", ".tgz")):
        with tarfile.open(archive) as tf:
            _extract_tar(tf, dest, strip_root)
    else:
        raise ValueError(f"Unknown archive format: {name}")


def _extract_zip(zf: zipfile.ZipFile, dest: Path, strip_root: bool) -> None:
    members = zf.namelist()
    root = _common_root(members) if strip_root else ""
    for member in members:
        rel = member[len(root):] if root else member
        if not rel:
            continue
        target = dest / rel
        if member.endswith("/"):
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                shutil.copyfileobj(src, dst)


def _extract_tar(tf: tarfile.TarFile, dest: Path, strip_root: bool) -> None:
    members = tf.getmembers()
    names = [m.name for m in members]
    root = _common_root(names) if strip_root else ""
    for member in members:
        rel = member.name[len(root):] if root else member.name
        if not rel:
            continue
        member.name = rel
        tf.extract(member, dest, filter="data")


def _common_root(names: list[str]) -> str:
    if not names:
        return ""
    parts = names[0].split("/")
    if len(parts) > 1 and all(n.startswith(parts[0] + "/") for n in names if n):
        return parts[0] + "/"
    return ""


def is_installed(tools_dir: Path, tool: str) -> bool:
    return (tools_dir / tool / ".installed").exists()


def mark_installed(tools_dir: Path, tool: str, version: str) -> None:
    marker = tools_dir / tool / ".installed"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(version)
