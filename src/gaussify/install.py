"""
Binary downloader — fetches ffmpeg, COLMAP 4.0+ (includes global_mapper/GLOMAP), and Brush into .tools/.
"""
import typer
from gaussify.tools.ffmpeg import install_ffmpeg
from gaussify.tools.colmap import install_colmap
from gaussify.tools.brush import install_brush
from gaussify.toolpaths import TOOLS_DIR, GITIGNORE_PATH


def install_tools() -> None:
    _ensure_gitignore()
    typer.echo("Installing tools into .tools/ ...")

    install_ffmpeg(TOOLS_DIR)
    install_colmap(TOOLS_DIR)
    install_brush(TOOLS_DIR)

    typer.echo("All tools installed. Run `gaussify run <video>` to get started.")


def _ensure_gitignore() -> None:
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if not GITIGNORE_PATH.exists():
        GITIGNORE_PATH.write_text(".tools/\n")
    else:
        content = GITIGNORE_PATH.read_text()
        if ".tools/" not in content:
            GITIGNORE_PATH.write_text(content + "\n.tools/\n")
