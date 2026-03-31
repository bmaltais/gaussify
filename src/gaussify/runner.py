"""
Shell runner — executes a tool subprocess, streams output, fails with clear attribution.
"""
import subprocess
import sys
import typer
from typing import List


def run_tool(stage: str, cmd: List[str]) -> None:
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
    except FileNotFoundError:
        typer.echo(f"\n[{stage}] Error: binary not found: {cmd[0]}", err=True)
        typer.echo("Run `gaussify install` to download all required tools.", err=True)
        raise typer.Exit(1)

    if result.returncode != 0:
        typer.echo(f"\n[{stage}] failed (exit code {result.returncode})", err=True)
        typer.echo(f"Command: {' '.join(cmd)}", err=True)
        raise typer.Exit(result.returncode)
