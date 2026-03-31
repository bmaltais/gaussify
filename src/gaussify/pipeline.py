"""
Pipeline orchestrator — runs each stage sequentially, fails fast with clear attribution.
"""
import typer
from pathlib import Path
from typing import Optional
from gaussify.gpu import detect_gpu
from gaussify.toolpaths import TOOLS_DIR
from gaussify.tools.ffmpeg import extract_frames, probe_duration
from gaussify.tools.colmap import run_colmap, run_global_mapper
from gaussify.tools.brush import run_brush


def run_pipeline(
    inputs: list[Path],
    output: Path,
    frames: int,
    gpu: Optional[str],
) -> None:
    for path in inputs:
        if not path.exists():
            typer.echo(f"Error: input file not found: {path}", err=True)
            raise typer.Exit(1)

    resolved_gpu = gpu or detect_gpu()
    typer.echo(f"GPU backend: {resolved_gpu}")

    _check_tools_installed()

    output.mkdir(parents=True, exist_ok=True)
    frames_dir = output / "images"
    sparse_dir = output / "sparse"
    _run_stage("frame extraction", _extract_all, inputs, frames_dir, frames)
    _run_stage("colmap", run_colmap, TOOLS_DIR, frames_dir, sparse_dir)
    _run_stage("colmap global_mapper", run_global_mapper, TOOLS_DIR, frames_dir, sparse_dir)

    typer.echo(f"\nSfM complete. Opening Brush GUI with scene: {output}")
    typer.echo("  Start training in the GUI. Your .ply will be saved where you choose.")
    _run_stage("brush", run_brush, TOOLS_DIR, output, resolved_gpu)


def _extract_all(inputs: list[Path], frames_dir: Path, total_frames: int) -> None:
    """Distribute total_frames across videos proportionally to duration into a flat frames dir."""
    frames_dir.mkdir(parents=True, exist_ok=True)

    durations = [probe_duration(v) for v in inputs]
    total_duration = sum(d for d in durations if d)

    for i, (video, duration) in enumerate(zip(inputs, durations)):
        if total_duration and duration:
            count = max(1, round(total_frames * duration / total_duration))
        else:
            count = total_frames // len(inputs)

        dur_str = f"{duration:.1f}s" if duration else "unknown duration"
        typer.echo(f"\n  [{i+1}/{len(inputs)}] {video.name} ({dur_str}) -> {count} frames")
        # Prefix ensures unique filenames across videos: v00_00001.png, v01_00001.png, ...
        extract_frames(video, frames_dir, count, prefix=f"v{i:02d}_")


def _run_stage(name: str, fn, *args, **kwargs) -> None:
    typer.echo(f"\n[{name}] starting...")
    fn(*args, **kwargs)
    typer.echo(f"[{name}] done.")


def _check_tools_installed() -> None:
    if not TOOLS_DIR.exists():
        typer.echo(
            "Error: tools not installed. Run `gaussify install` first.", err=True
        )
        raise typer.Exit(1)
