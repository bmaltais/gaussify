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


REPO = "colmap/colmap"


def install_colmap(tools_dir: Path) -> None:
    if is_installed(tools_dir, "colmap"):
        typer.echo("  colmap: already installed, skipping.")
        return

    system = platform.system()
    if system != "Windows":
        typer.echo(
            f"  colmap: no pre-built binary for {system}.\n"
            "  Linux: install via `sudo apt install colmap` or build from source.\n"
            "  macOS: install via `brew install colmap`.",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo("  colmap: fetching latest release info...")
    release = get_latest_release(REPO)
    tag = release["tag_name"]

    gpu = _detect_cuda()
    suffix = "cuda" if gpu else "nocuda"
    asset_name = f"colmap-x64-windows-{suffix}.zip"
    asset = pick_asset(release["assets"], asset_name)

    if not asset:
        typer.echo(f"  colmap: asset '{asset_name}' not found in {tag}", err=True)
        raise typer.Exit(1)

    typer.echo(f"  colmap: downloading {asset['name']} ({asset['size'] // 1024 // 1024} MB)...")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset["name"]
        download(asset["browser_download_url"], archive)
        typer.echo("  colmap: extracting...")
        extract(archive, tools_dir / "colmap")

    mark_installed(tools_dir, "colmap", tag)
    typer.echo("  colmap: done.")


def run_colmap(tools_dir: Path, frames_dir: Path, sparse_dir: Path) -> None:
    from gaussify.runner import run_tool
    sparse_dir.mkdir(parents=True, exist_ok=True)
    db = sparse_dir / "database.db"
    colmap = _colmap_bin(tools_dir)

    run_tool("colmap feature_extractor", [
        str(colmap), "feature_extractor",
        "--database_path", str(db),
        "--image_path", str(frames_dir),
        "--ImageReader.single_camera", "1",
    ])
    run_tool("colmap exhaustive_matcher", [
        str(colmap), "exhaustive_matcher",
        "--database_path", str(db),
    ])


def _colmap_bin(tools_dir: Path) -> Path:
    exe = "colmap.exe" if platform.system() == "Windows" else "colmap"
    return tools_dir / "colmap" / "bin" / exe


def _detect_cuda() -> bool:
    import subprocess
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
