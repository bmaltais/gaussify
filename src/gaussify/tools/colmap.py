from pathlib import Path
from gaussify.runner import run_tool


def install_colmap(tools_dir: Path) -> None:
    raise NotImplementedError("COLMAP installer not yet implemented")


def run_colmap(tools_dir: Path, frames_dir: Path, sparse_dir: Path) -> None:
    sparse_dir.mkdir(parents=True, exist_ok=True)
    colmap = _colmap_bin(tools_dir)
    run_tool("colmap feature_extractor", [
        str(colmap), "feature_extractor",
        "--database_path", str(sparse_dir / "database.db"),
        "--image_path", str(frames_dir),
    ])
    run_tool("colmap exhaustive_matcher", [
        str(colmap), "exhaustive_matcher",
        "--database_path", str(sparse_dir / "database.db"),
    ])


def _colmap_bin(tools_dir: Path) -> Path:
    import platform
    exe = "colmap.exe" if platform.system() == "Windows" else "colmap"
    return tools_dir / "colmap" / "bin" / exe
