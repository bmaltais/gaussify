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


def probe_duration(input: Path) -> float | None:
    """Return video duration in seconds, or None if it cannot be determined."""
    import subprocess
    result = subprocess.run(
        [str(_ffprobe_bin()), "-v", "quiet", "-show_entries", "format=duration",
         "-of", "csv=p=0", str(input)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip()) if result.returncode == 0 else None
    except ValueError:
        return None


def extract_frames(input: Path, frames_dir: Path, count: int, prefix: str = "") -> None:
    import subprocess
    from gaussify.runner import run_tool
    frames_dir.mkdir(parents=True, exist_ok=True)

    duration = probe_duration(input)

    if duration and duration > 0:
        # Probe native fps to get total frame count and avoid over-sampling
        fps_probe = subprocess.run(
            [str(ffprobe), "-v", "quiet", "-select_streams", "v:0",
             "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(input)],
            capture_output=True, text=True,
        )
        native_fps = _parse_fps(fps_probe.stdout.strip()) if fps_probe.returncode == 0 else None
        total_frames = int(native_fps * duration) if native_fps else None

        if total_frames and count >= total_frames:
            typer.echo(f"  Video has ~{total_frames} frames total — extracting all of them...")
            vf = None  # extract every frame, no fps filter
        else:
            fps = count / duration
            typer.echo(f"  Extracting {count} frames evenly over {duration:.1f}s (~{fps:.2f} fps)...")
            vf = f"fps={fps}"
    else:
        # Fallback: first N frames
        typer.echo(f"  Could not probe duration — extracting first {count} frames...")
        vf = None

    cmd = [str(_ffmpeg_bin()), "-i", str(input)]
    if vf:
        cmd += ["-vf", vf, "-vsync", "vfr"]
    cmd += ["-q:v", "2", str(frames_dir / f"{prefix}%05d.png")]

    run_tool("frame extraction", cmd)


def _parse_fps(rate_str: str) -> float | None:
    """Parse ffprobe r_frame_rate output like '30000/1001' or '30'."""
    try:
        if "/" in rate_str:
            num, den = rate_str.split("/")
            return float(num) / float(den)
        return float(rate_str)
    except (ValueError, ZeroDivisionError):
        return None


def _ffmpeg_bin() -> Path:
    return _find_bin("ffmpeg")


def _ffprobe_bin() -> Path:
    return _find_bin("ffprobe")


def _find_bin(name: str) -> Path:
    from gaussify.toolpaths import TOOLS_DIR
    exe = f"{name}.exe" if platform.system() == "Windows" else name
    candidates = [
        TOOLS_DIR / "ffmpeg" / "bin" / exe,
        TOOLS_DIR / "ffmpeg" / exe,
    ]
    for c in candidates:
        if c.exists():
            return c
    return candidates[0]  # will fail at runtime with clear error from runner
