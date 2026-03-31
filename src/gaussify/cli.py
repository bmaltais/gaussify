import typer
from pathlib import Path
from typing import Optional
from gaussify.install import install_tools
from gaussify.pipeline import run_pipeline

app = typer.Typer(help="Gaussian splatting pipeline from video to .splat")


@app.command()
def install():
    """Download and install all required tools into .tools/."""
    install_tools()


@app.command()
def run(
    inputs: list[Path] = typer.Argument(..., help="One or more input video files"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    frames: int = typer.Option(200, "--frames", "-f", help="Total frames to extract across all videos"),
    gpu: Optional[str] = typer.Option(None, "--gpu", help="GPU backend: cuda, rocm, or cpu"),
):
    """Run the full pipeline: video(s) → frames → SfM → 3DGS → .splat"""
    run_pipeline(inputs=inputs, output=output, frames=frames, gpu=gpu)


def main():
    app()
