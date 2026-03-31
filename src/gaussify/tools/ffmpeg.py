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


REPO = "BtbN/FFmpeg-Builds"

_PLATFORM_SUBSTRINGS = {
    # (os, arch) → substrings that must appear in the asset name
    ("Windows", "AMD64"): ("win64-gpl", ".zip"),
    ("Linux",   "x86_64"): ("linux64-gpl", ".tar.xz"),
}


def install_ffmpeg(tools_dir: Path) -> None:
    if is_installed(tools_dir, "ffmpeg"):
        typer.echo("  ffmpeg: already installed, skipping.")
        return

    system = platform.system()
    arch = platform.machine()

    if (system, arch) not in _PLATFORM_SUBSTRINGS:
        typer.echo(
            f"  ffmpeg: no pre-built binary for {system}/{arch}.\n"
            "  macOS: install via `brew install ffmpeg` then re-run.",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo("  ffmpeg: fetching latest release info...")
    release = get_latest_release(REPO)
    tag = release["tag_name"]
    substrings = _PLATFORM_SUBSTRINGS[(system, arch)]
    # Prefer stable n8.x builds over nightly
    asset = pick_asset(
        [a for a in release["assets"] if a["name"].startswith("ffmpeg-n8")],
        *substrings,
    ) or pick_asset(release["assets"], *substrings)

    if not asset:
        typer.echo(f"  ffmpeg: no matching asset for {system}/{arch} in {tag}", err=True)
        raise typer.Exit(1)

    typer.echo(f"  ffmpeg: downloading {asset['name']} ({asset['size'] // 1024 // 1024} MB)...")
    with tempfile.TemporaryDirectory() as tmp:
        archive = Path(tmp) / asset["name"]
        download(asset["browser_download_url"], archive)
        typer.echo("  ffmpeg: extracting...")
        extract(archive, tools_dir / "ffmpeg")

    mark_installed(tools_dir, "ffmpeg", tag)
    typer.echo("  ffmpeg: done.")


def extract_frames(input: Path, frames_dir: Path, count: int) -> None:
    from gaussify.runner import run_tool
    frames_dir.mkdir(parents=True, exist_ok=True)
    run_tool(
        "frame extraction",
        [
            str(_ffmpeg_bin()),
            "-i", str(input),
            "-vframes", str(count),
            "-q:v", "2",
            str(frames_dir / "%05d.png"),
        ],
    )


def _ffmpeg_bin() -> Path:
    from gaussify.toolpaths import TOOLS_DIR
    exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    # BtbN zip extracts bin/ subdir on Windows, bin/ on Linux
    candidates = [
        TOOLS_DIR / "ffmpeg" / "bin" / exe,
        TOOLS_DIR / "ffmpeg" / exe,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # will fail at runtime with clear error from runner
