"""
Pipeline orchestrator — runs each stage sequentially, fails fast with clear attribution.
"""
import typer
from pathlib import Path
from typing import Optional
from gaussify.gpu import detect_gpu
from gaussify.toolpaths import TOOLS_DIR
from gaussify.tools.ffmpeg import extract_frames
from gaussify.tools.colmap import run_colmap
from gaussify.tools.glomap import run_glomap
from gaussify.tools.brush import run_brush


def run_pipeline(
    input: Path,
    output: Path,
    frames: int,
    gpu: Optional[str],
) -> None:
    if not input.exists():
        typer.echo(f"Error: input file not found: {input}", err=True)
        raise typer.Exit(1)

    resolved_gpu = gpu or detect_gpu()
    typer.echo(f"GPU backend: {resolved_gpu}")

    _check_tools_installed()

    output.mkdir(parents=True, exist_ok=True)
    frames_dir = output / "frames"
    sparse_dir = output / "sparse"
    splat_path = output / "scene.splat"

    _run_stage("frame extraction", extract_frames, input, frames_dir, frames)
    _run_stage("colmap", run_colmap, TOOLS_DIR, frames_dir, sparse_dir)
    _run_stage("glomap", run_glomap, TOOLS_DIR, sparse_dir)
    _run_stage("brush", run_brush, TOOLS_DIR, sparse_dir, splat_path, resolved_gpu)

    typer.echo(f"\nDone. Output: {splat_path}")


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
