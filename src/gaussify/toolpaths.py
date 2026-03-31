"""
Canonical paths — all tool locations resolved from here.
"""
from pathlib import Path

# Root of the project (where gaussify is invoked from)
PROJECT_ROOT = Path.cwd()
TOOLS_DIR = PROJECT_ROOT / ".tools"
GITIGNORE_PATH = PROJECT_ROOT / ".gitignore"
