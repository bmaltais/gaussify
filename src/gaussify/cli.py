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
    input: Path = typer.Argument(..., help="Input video file"),
    output: Path = typer.Option(Path("./output"), "--output", "-o", help="Output directory"),
    frames: int = typer.Option(200, "--frames", "-f", help="Number of frames to extract"),
    gpu: Optional[str] = typer.Option(None, "--gpu", help="GPU backend: cuda, rocm, or cpu"),
):
    """Run the full pipeline: video → frames → SfM → 3DGS → .splat"""
    run_pipeline(input=input, output=output, frames=frames, gpu=gpu)


def main():
    app()
