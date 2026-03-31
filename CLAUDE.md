# gaussify

CLI tool that takes a video file and produces a Gaussian splat (.splat) in one command.
Full PRD: https://github.com/bmaltais/gaussify/issues/1

## Pipeline

```
gaussify install          # one-time: downloads all binaries into .tools/
gaussify run input.mp4 --output ./my-scene --frames 200 --gpu cuda
  ffmpeg      → extract N frames as PNG
  COLMAP      → feature extraction + exhaustive matching (SfM)
  GLOMAP      → mapper (accelerated SfM, requires COLMAP for matching)
  Brush       → 3DGS training → scene.splat
```

## Key Design Decisions

- **Binary isolation**: all native binaries live in `.tools/` inside the project. No PATH changes, no global installs. `.tools/` is gitignored.
- **uv only**: Python toolchain managed by uv. `uv` is the sole bootstrap requirement.
- **GPU auto-detect**: `gpu.py` detects cuda/rocm/cpu at runtime. User can override with `--gpu`.
- **Fail fast, no magic**: when a stage fails, print stage name + raw tool output and exit. No retries.
- **Idempotent install**: each tool writes `.tools/<tool>/.installed` on success. Re-running `install` skips already-installed tools.
- **Frame extraction**: ffmpeg only — Blender is not in the pipeline.
- **3DGS engine**: Brush (https://github.com/ArthurBrussee/brush), not the tool shown in reference tutorials.

## Platform Matrix

| Tool   | Windows x64 | Linux x64 | macOS arm64 |
|--------|-------------|-----------|-------------|
| ffmpeg | BtbN GPL static | BtbN GPL static | brew (manual) |
| COLMAP | cuda/nocuda auto | apt/build-from-source msg | brew msg |
| GLOMAP | cuda/nocuda auto | build-from-source msg | build-from-source msg |
| Brush  | msvc binary | linux-gnu binary | apple-darwin binary |

## Architecture

```
src/gaussify/
  cli.py          # typer entrypoint: install + run commands
  pipeline.py     # sequential orchestrator: ffmpeg → colmap → glomap → brush
  install.py      # bootstrapper: calls each tool installer, ensures .gitignore
  downloader.py   # shared: GitHub API, asset picker, download+extract, install markers
  gpu.py          # cuda/rocm/cpu detection
  runner.py       # subprocess wrapper: prints stage name + raw output on failure
  toolpaths.py    # TOOLS_DIR and GITIGNORE_PATH resolved from cwd
  tools/
    ffmpeg.py     # install_ffmpeg() + extract_frames()
    colmap.py     # install_colmap() + run_colmap()
    glomap.py     # install_glomap() + run_glomap()
    brush.py      # install_brush() + run_brush()
```

## Current State (2026-03-31)

- [x] Project scaffold (typer CLI, uv, pytest)
- [x] GPU detection (tests passing)
- [x] Binary downloaders for all 4 tools (tests passing)
- [ ] End-to-end install test on real machine
- [ ] End-to-end run test on real video
- [ ] Phase 2: GUI

## Running Tests

```bash
uv run pytest tests/ -v
```

## Next Steps

1. Run `gaussify install` on a real machine and fix any extraction/path issues
2. Run `gaussify run` on a real video and validate full pipeline
3. Add `gaussify doctor` command (check tool presence, GPU, print versions)
