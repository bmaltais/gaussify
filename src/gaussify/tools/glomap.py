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


REPO = "colmap/glomap"


def install_glomap(tools_dir: Path) -> None:
    if is_installed(tools_dir, "glomap"):
        typer.echo("  glomap: already installed, skipping.")
        return

    system = platform.system()
    if system != "Windows":
        typer.echo(
            f"  glomap: no pre-built binary for {system}.\n"
            "  Linux/macOS: build from source at https://github.com/colmap/glomap",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo("  glomap: fetching latest release info...")
    release = get_latest_release(REPO)
    tag = release["tag_name"]

    gpu = _detect_cuda()
    suffix = "cuda" if gpu else "nocuda"
    asset_name = f"glomap-x64-windows-{suffix}.zip"
    asset = pick_asset(release["assets"], asset_name)

    if not asset:
        typer.echo(f"  glomap: asset '{asset_name}' not found in {tag}", err=True)
        raise typer.Exit(1)

    typer.echo(f"  glomap: downloading {asset['name']} ({asset['size'] // 1024 // 1024} MB)...")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset["name"]
        download(asset["browser_download_url"], archive)
        typer.echo("  glomap: extracting...")
        extract(archive, tools_dir / "glomap")

    mark_installed(tools_dir, "glomap", tag)
    typer.echo("  glomap: done.")


def run_glomap(tools_dir: Path, sparse_dir: Path) -> None:
    from gaussify.runner import run_tool
    glomap = _glomap_bin(tools_dir)
    frames_dir = sparse_dir.parent / "frames"
    run_tool("glomap mapper", [
        str(glomap), "mapper",
        "--database_path", str(sparse_dir / "database.db"),
        "--image_path", str(frames_dir),
        "--output_path", str(sparse_dir),
    ])


def _glomap_bin(tools_dir: Path) -> Path:
    exe = "glomap.exe" if platform.system() == "Windows" else "glomap"
    return tools_dir / "glomap" / "bin" / exe


def _detect_cuda() -> bool:
    import subprocess
    try:
        result = subprocess.run(["nvidia-smi"], capture_output=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False
