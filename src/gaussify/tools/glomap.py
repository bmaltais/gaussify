from pathlib import Path
from gaussify.runner import run_tool


def install_glomap(tools_dir: Path) -> None:
    raise NotImplementedError("GLOMAP installer not yet implemented")


def run_glomap(tools_dir: Path, sparse_dir: Path) -> None:
    glomap = _glomap_bin(tools_dir)
    run_tool("glomap", [
        str(glomap), "mapper",
        "--database_path", str(sparse_dir / "database.db"),
        "--image_path", str(sparse_dir / ".." / "frames"),
        "--output_path", str(sparse_dir),
    ])


def _glomap_bin(tools_dir: Path) -> Path:
    import platform
    exe = "glomap.exe" if platform.system() == "Windows" else "glomap"
    return tools_dir / "glomap" / "bin" / exe
