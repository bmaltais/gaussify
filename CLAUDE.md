# gaussify

CLI tool that takes video footage and produces a Gaussian splat in one command.
Full PRD: https://github.com/bmaltais/gaussify/issues/1

## Pipeline

```
gaussify install          # one-time: downloads all binaries into .tools/
gaussify install --densify  # also install RoMa v2 densifier
gaussify run input.mp4 --output ./my-scene --frames 200 --gpu cuda
gaussify run input.mp4 --output ./my-scene --densify --quality high
  ffmpeg      → extract N frames evenly distributed (proportional for multi-video)
  COLMAP      → feature extraction + exhaustive matching
  COLMAP      → view_graph_calibrator (focal length priors for PNG frames)
  COLMAP      → global_mapper (integrated GLOMAP — replaces standalone GLOMAP)
  [densify]   → RoMa v2 dense point cloud init (optional --densify flag)
  Brush       → opens GUI with COLMAP project loaded (--with-viewer)
```

## Key Design Decisions

- **Binary isolation**: all native binaries live in `.tools/` inside the project. No PATH changes, no global installs. `.tools/` is gitignored.
- **uv only**: Python toolchain managed by uv. `uv` is the sole bootstrap requirement.
- **GPU auto-detect**: `gpu.py` detects cuda/rocm/cpu at runtime. User can override with `--gpu`.
- **Fail fast, no magic**: when a stage fails, print stage name + full command + raw tool output and exit. No retries.
- **Idempotent install**: each tool writes `.tools/<tool>/.installed` on success. Re-running `install` skips already-installed tools.
- **Frame extraction**: ffmpeg only. Frames distributed proportionally by duration across multiple inputs.
- **Output layout**: standard COLMAP project (`images/` + `sparse/0/`) — compatible with LichtFeld Studio, nerfstudio, and other tools.
- **GLOMAP**: standalone binary dropped; COLMAP 4.0+ ships `global_mapper` built-in (avoids DB schema incompatibility).
- **Brush**: opens GUI with `--with-viewer`; user drives training interactively. Exports `.ply`.
- **Densify**: optional RoMa v2 step (Lichtfeld-Densification-Plugin) installed via git+uv. Produces `points3D_dense.ply` for better Brush initialization.

## Platform Matrix

| Tool    | Windows x64 | Linux x64 | macOS arm64 |
|---------|-------------|-----------|-------------|
| ffmpeg  | BtbN GPL static | BtbN GPL static | brew (manual) |
| COLMAP  | cuda/nocuda auto | apt/build-from-source msg | brew msg |
| Brush   | msvc binary | linux-gnu binary | apple-darwin binary |
| densify | git + uv | git + uv | git + uv |

## Architecture

```
src/gaussify/
  cli.py          # typer entrypoint: install (--densify) + run (--densify, --quality)
  pipeline.py     # sequential orchestrator: ffmpeg → colmap → [densify] → brush
  install.py      # bootstrapper: calls each tool installer, ensures .gitignore
  downloader.py   # shared: GitHub API, asset picker, download+extract, install markers
  gpu.py          # cuda/rocm/cpu detection
  runner.py       # subprocess wrapper: prints command + stage name + raw output on failure
  toolpaths.py    # TOOLS_DIR and GITIGNORE_PATH resolved from cwd
  tools/
    ffmpeg.py     # install_ffmpeg() + extract_frames() + probe_duration()
    colmap.py     # install_colmap() + run_colmap() + run_global_mapper()
    brush.py      # install_brush() + run_brush()
    densify.py    # install_densify() + run_densify() — optional RoMa v2 step
```

## Current State (2026-03-31)

- [x] Project scaffold (typer CLI, uv, pytest)
- [x] GPU detection (tests passing)
- [x] Binary downloaders for ffmpeg, COLMAP, Brush
- [x] End-to-end pipeline working on real videos
- [x] Multi-video support with proportional frame distribution
- [x] view_graph_calibrator for better focal length priors
- [x] Standard COLMAP output layout (images/ + sparse/0/)
- [x] Full CLI command echoed before each tool invocation
- [x] Optional densify step (RoMa v2 via Lichtfeld-Densification-Plugin)
- [ ] End-to-end densify test on real scene
- [ ] Phase 2: GUI

## Running Tests

```bash
uv run pytest tests/ -v
```

## Next Steps

1. Test `gaussify install --densify` and `gaussify run --densify` end-to-end
2. Add `gaussify doctor` command (check tool presence, GPU, print versions)
3. Phase 2: GUI
