from pathlib import Path
from gaussify.runner import run_tool


def install_ffmpeg(tools_dir: Path) -> None:
    raise NotImplementedError("ffmpeg installer not yet implemented")


def extract_frames(input: Path, frames_dir: Path, count: int) -> None:
    frames_dir.mkdir(parents=True, exist_ok=True)
    ffmpeg = _ffmpeg_bin()
    run_tool(
        "frame extraction",
        [str(ffmpeg), "-i", str(input), "-vframes", str(count), str(frames_dir / "%05d.png")],
    )


def _ffmpeg_bin() -> Path:
    from gaussify.toolpaths import TOOLS_DIR
    import platform
    exe = "ffmpeg.exe" if platform.system() == "Windows" else "ffmpeg"
    return TOOLS_DIR / "ffmpeg" / exe
