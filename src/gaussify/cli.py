import typer
from pathlib import Path
from typing import Optional
from gaussify.install import install_tools
from gaussify.pipeline import run_pipeline
from gaussify.tools.densify import QUALITY_PROFILES, DEFAULT_QUALITY

app = typer.Typer(help="Gaussian splatting pipeline from video to .splat")


@app.command()
def install(
    densify: bool = typer.Option(False, "--densify", help="Also install the densify step (requires git + CUDA)"),
):
    """Download and install all required tools into .tools/."""
    install_tools(with_densify=densify)


@app.command()
def run(
    inputs: list[Path] = typer.Argument(..., help="One or more input video files"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    frames: int = typer.Option(200, "--frames", "-f", help="Total frames to extract across all videos"),
    gpu: Optional[str] = typer.Option(None, "--gpu", help="GPU backend: cuda, rocm, or cpu"),
    densify: bool = typer.Option(False, "--densify", help="Run dense point cloud init after SfM (requires densify install)"),
    quality: str = typer.Option(DEFAULT_QUALITY, "--quality", "-q", help=f"Densify quality: {', '.join(QUALITY_PROFILES)}"),
):
    """Run the full pipeline: video(s) → frames → SfM → [densify] → 3DGS"""
    run_pipeline(inputs=inputs, output=output, frames=frames, gpu=gpu, densify=densify, quality=quality)


def main():
    app()
