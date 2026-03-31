from pathlib import Path
from gaussify.runner import run_tool


def install_brush(tools_dir: Path) -> None:
    raise NotImplementedError("Brush installer not yet implemented")


def run_brush(tools_dir: Path, sparse_dir: Path, splat_path: Path, gpu: str) -> None:
    brush = _brush_bin(tools_dir, gpu)
    run_tool("brush", [
        str(brush), "train",
        "--colmap", str(sparse_dir),
        "--output", str(splat_path),
    ])


def _brush_bin(tools_dir: Path, gpu: str) -> Path:
    import platform
    exe = "brush.exe" if platform.system() == "Windows" else "brush"
    return tools_dir / f"brush-{gpu}" / exe
