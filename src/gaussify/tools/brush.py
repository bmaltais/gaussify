import platform
import tempfile
from pathlib import Path

import typer

from gaussify.downloader import (
    download,
    extract,
    get_latest_release,
    is_installed,
    mark_installed,
    pick_asset,
)


REPO = "ArthurBrussee/brush"

_PLATFORM_ASSET = {
    ("Windows", "AMD64"): "x86_64-pc-windows-msvc.zip",
    ("Linux",   "x86_64"): "x86_64-unknown-linux-gnu.tar.xz",
    ("Darwin",  "arm64"): "aarch64-apple-darwin.tar.xz",
}


def install_brush(tools_dir: Path) -> None:
    if is_installed(tools_dir, "brush"):
        typer.echo("  brush: already installed, skipping.")
        return

    system = platform.system()
    arch = platform.machine()
    key = (system, arch)

    if key not in _PLATFORM_ASSET:
        typer.echo(
            f"  brush: no pre-built binary for {system}/{arch}.\n"
            "  See https://github.com/ArthurBrussee/brush/releases for manual install.",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo("  brush: fetching latest release info...")
    release = get_latest_release(REPO)
    tag = release["tag_name"]
    suffix = _PLATFORM_ASSET[key]
    asset = pick_asset(release["assets"], "brush-app-", suffix)

    if not asset:
        typer.echo(f"  brush: no matching asset for {system}/{arch} in {tag}", err=True)
        raise typer.Exit(1)

    typer.echo(f"  brush: downloading {asset['name']} ({asset['size'] // 1024 // 1024} MB)...")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset["name"]
        download(asset["browser_download_url"], archive)
        typer.echo("  brush: extracting...")
        extract(archive, tools_dir / "brush")

    mark_installed(tools_dir, "brush", tag)
    typer.echo("  brush: done.")


def run_brush(tools_dir: Path, sparse_dir: Path, splat_path: Path, gpu: str) -> None:
    from gaussify.runner import run_tool
    brush = _brush_bin(tools_dir)
    run_tool("brush", [
        str(brush), "train",
        "--source", str(sparse_dir),
        "--export-path", str(splat_path),
    ])


def _brush_bin(tools_dir: Path) -> Path:
    exe = "brush_app.exe" if platform.system() == "Windows" else "brush_app"
    candidates = [
        tools_dir / "brush" / exe,
        tools_dir / "brush" / "bin" / exe,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]
