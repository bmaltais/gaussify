"""
Dense point cloud initializer — uses RoMa v2 matching to produce a denser
initialization for Brush, improving training speed and quality.

Clones the Lichtfeld-Densification-Plugin repo into .tools/densify/ and runs
densify.py as a subprocess via uv.
"""
import platform
import subprocess
import sys
from pathlib import Path

import typer

from gaussify.downloader import is_installed, mark_installed

REPO_URL = "https://github.com/shadygm/Lichtfeld-Densification-Plugin.git"
DENSIFY_DIR_NAME = "densify"

QUALITY_PROFILES = ("turbo", "fast", "base", "high", "precise")
DEFAULT_QUALITY = "fast"


def install_densify(tools_dir: Path) -> None:
    if is_installed(tools_dir, DENSIFY_DIR_NAME):
        typer.echo("  densify: already installed, skipping.")
        return

    dest = tools_dir / DENSIFY_DIR_NAME

    typer.echo("  densify: cloning Lichtfeld-Densification-Plugin...")
    result = subprocess.run(
        ["git", "clone", "--depth=1", REPO_URL, str(dest)],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        typer.echo("  densify: git clone failed.", err=True)
        raise typer.Exit(1)

    _patch_densify(dest)

    typer.echo("  densify: creating Python 3.12 venv (open3d requires <=3.12)...")
    venv = dest / ".venv"
    result = subprocess.run(
        ["uv", "venv", "--python", "3.12", str(venv)],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        typer.echo("  densify: failed to create venv with Python 3.12.", err=True)
        typer.echo("  Install Python 3.12 with: uv python install 3.12", err=True)
        raise typer.Exit(1)

    typer.echo("  densify: installing Python dependencies via uv...")
    result = subprocess.run(
        ["uv", "pip", "install", "--python", str(venv),
         "torch", "torchvision", "numpy==2.4.1", "pycolmap", "Pillow",
         "scipy", "tqdm", "einops>=0.8.1", "rich>=14.2.0", "open3d",
         "--extra-index-url", "https://download.pytorch.org/whl/cu128"],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        typer.echo("  densify: dependency install failed.", err=True)
        raise typer.Exit(1)

    _install_lichtfeld_stub(venv)

    mark_installed(tools_dir, DENSIFY_DIR_NAME, "latest")
    typer.echo("  densify: done.")


_LICHTFELD_STUB = """\
\"\"\"Stub for lichtfeld host API — used when running densify standalone.\"\"\"
import logging as _logging

_logger = _logging.getLogger("lichtfeld")
_logger.propagate = False
if not _logger.handlers:
    _logger.addHandler(_logging.StreamHandler())
    _logger.setLevel(_logging.INFO)

class _Log:
    def info(self, msg):  _logger.info(msg)
    def warn(self, msg):  _logger.warning(msg)
    def debug(self, msg): _logger.debug(msg)
    def error(self, msg): _logger.error(msg)

log = _Log()
"""


def _patch_densify(dest: Path) -> None:
    """Patch densify.py to run standalone (outside LichtFeld Studio):
    1. Fix relative imports (.core.*  →  core.*) — needed when run as a script.
    2. Drop a lichtfeld stub into the venv site-packages after venv creation.
    """
    densify_py = dest / "densify.py"
    content = densify_py.read_text(encoding="utf-8")

    # Fix relative imports
    patched = content.replace("from .core.", "from core.")

    # Remove the top-level `import lichtfeld as lf` — stub goes into site-packages instead
    patched = patched.replace("import lichtfeld as lf\n", "")

    if patched == content:
        typer.echo("  densify: warning — patches not applied (source may have changed).", err=True)
    else:
        densify_py.write_text(patched, encoding="utf-8")
        typer.echo("  densify: patched relative imports.")


def _install_lichtfeld_stub(venv: Path) -> None:
    """Write the lichtfeld stub into the venv so core/*.py can import it."""
    # site-packages location differs by OS
    import platform
    if platform.system() == "Windows":
        site_packages = venv / "Lib" / "site-packages"
    else:
        # e.g. lib/python3.12/site-packages
        lib = venv / "lib"
        py_dirs = sorted(lib.glob("python3.*"))
        site_packages = py_dirs[0] / "site-packages" if py_dirs else lib / "site-packages"

    site_packages.mkdir(parents=True, exist_ok=True)
    stub = site_packages / "lichtfeld.py"
    stub.write_text(_LICHTFELD_STUB, encoding="utf-8")
    typer.echo("  densify: installed lichtfeld stub into venv.")


def run_densify(
    tools_dir: Path,
    output_dir: Path,
    quality: str = DEFAULT_QUALITY,
) -> None:
    """Run densify.py against the scene at output_dir (must contain images/ and sparse/)."""
    from gaussify.runner import run_tool

    if quality not in QUALITY_PROFILES:
        typer.echo(
            f"  densify: unknown quality '{quality}'. "
            f"Choose from: {', '.join(QUALITY_PROFILES)}",
            err=True,
        )
        raise typer.Exit(1)

    densify_script = tools_dir / DENSIFY_DIR_NAME / "densify.py"
    if not densify_script.exists():
        typer.echo(
            "  densify: densify.py not found. Run `gaussify install --densify`.",
            err=True,
        )
        raise typer.Exit(1)

    python = _python_bin(tools_dir)

    run_tool("densify", [
        str(python), str(densify_script),
        "--scene_root", str(output_dir),
        "--images_subdir", "images",   # our frames live in images/ not images_2/
        "--roma_setting", quality,
        "--out_name", "points3D_dense.ply",
    ])

    dense_ply = output_dir / "sparse" / "0" / "points3D_dense.ply"
    if dense_ply.exists():
        typer.echo(f"  densify: dense point cloud written to {dense_ply}")
        _convert_ply_to_bin(tools_dir, dense_ply)
    else:
        typer.echo("  densify: warning — expected output not found.", err=True)


def _convert_ply_to_bin(tools_dir: Path, dense_ply: Path) -> None:
    """Replace points3D.bin with the dense point cloud so Brush uses it as initialization."""
    points3d_bin = dense_ply.parent / "points3D.bin"
    sparse_bin_backup = dense_ply.parent / "points3D_sparse.bin"
    python = _python_bin(tools_dir)

    # Inline script: reads the .ply via open3d, writes points3D.bin via pycolmap
    script = """
import sys, open3d as o3d, pycolmap, numpy as np
from pathlib import Path

ply_path = Path(sys.argv[1])
out_path = Path(sys.argv[2])
backup_path = Path(sys.argv[3])

pcd = o3d.io.read_point_cloud(str(ply_path))
xyz = np.asarray(pcd.points)
rgb = (np.asarray(pcd.colors) * 255).astype(np.uint8) if pcd.has_colors() else np.zeros((len(xyz), 3), dtype=np.uint8)

# Back up original sparse points3D.bin before overwriting
if out_path.exists() and not backup_path.exists():
    import shutil
    shutil.copy2(out_path, backup_path)

rec = pycolmap.Reconstruction()
rec.read(str(out_path.parent))
rec.points3D.clear()
for i, (pt, color) in enumerate(zip(xyz, rgb)):
    p3d = pycolmap.Point3D()
    p3d.xyz = pt
    p3d.color = color
    p3d.error = 0.0
    p3d.track = pycolmap.Track()
    rec.add_point3D(pt, pycolmap.Track(), color)
rec.write_binary(str(out_path.parent))
print(f"Written {len(xyz)} points to {out_path}")
"""

    typer.echo("  densify: converting dense .ply → points3D.bin for Brush...")
    result = subprocess.run(
        [str(python), "-c", script,
         str(dense_ply), str(points3d_bin), str(sparse_bin_backup)],
        capture_output=False,
        text=True,
    )
    if result.returncode != 0:
        typer.echo("  densify: warning — .ply → .bin conversion failed; Brush will use sparse points.", err=True)
    else:
        typer.echo(f"  densify: points3D.bin replaced (sparse backup: {sparse_bin_backup.name})")


def _python_bin(tools_dir: Path) -> Path:
    """Return the Python interpreter inside the densify venv, falling back to sys.executable."""
    venv = tools_dir / DENSIFY_DIR_NAME / ".venv"
    if platform.system() == "Windows":
        candidate = venv / "Scripts" / "python.exe"
    else:
        candidate = venv / "bin" / "python"
    return candidate if candidate.exists() else Path(sys.executable)
