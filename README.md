# gaussify

CLI tool that takes video footage and produces a Gaussian splat in one command.

## Requirements

- [uv](https://github.com/astral-sh/uv) — the only bootstrap dependency
- NVIDIA GPU with CUDA (recommended; CPU fallback is slow)
- Git (required only for `--densify`)

## Installation

```bash
# Core tools (ffmpeg, COLMAP 4.0+, Brush)
uv run gaussify install

# Core + dense point cloud initializer (requires git + CUDA)
uv run gaussify install --densify
```

All binaries are downloaded into `.tools/` inside the project directory — no PATH changes, no global installs.

## Usage

```bash
# Single video, default 200 frames
uv run gaussify run myvideo.mp4 --output ./my-scene

# Multiple videos, custom frame count
uv run gaussify run clip1.mp4 clip2.mp4 --output ./my-scene --frames 300

# With dense point cloud initialization (better quality, slower)
uv run gaussify run myvideo.mp4 --output ./my-scene --densify

# Full options
uv run gaussify run myvideo.mp4 --output ./my-scene --frames 200 --gpu cuda --densify --quality high
```

## Pipeline

```
ffmpeg               → extract N frames evenly distributed across video duration
colmap               → feature extraction + exhaustive matching
colmap               → view_graph_calibrator (focal length estimation for PNG frames)
colmap               → global_mapper (GLOMAP-based SfM — all camera poses + sparse point cloud)
[densify]            → RoMa v2 dense point cloud initialization (optional, --densify)
brush                → opens GUI with scene loaded, ready for 3DGS training
```

Frames are distributed **proportionally by duration** across multiple input videos.
Output is a standard **COLMAP project layout** — compatible with Brush, LichtFeld Studio, nerfstudio, and other 3DGS tools.

## Output layout

```
my-scene/
  images/              ← extracted frames (v00_00001.png, v01_00001.png, ...)
  sparse/
    database.db
    0/
      cameras.bin
      images.bin
      points3D.bin
      points3D_dense.ply   ← present only when --densify is used
```

## Options

### `gaussify install`

| Flag | Description |
|------|-------------|
| `--densify` | Also install the RoMa v2 densification tool |

### `gaussify run`

| Flag | Default | Description |
|------|---------|-------------|
| `--output`, `-o` | `./output` | Output directory |
| `--frames`, `-f` | `200` | Total frames to extract across all input videos |
| `--gpu` | auto-detect | Force GPU backend: `cuda`, `rocm`, or `cpu` |
| `--densify` | off | Run dense point cloud init after SfM |
| `--quality`, `-q` | `fast` | Densify quality: `turbo`, `fast`, `base`, `high`, `precise` |

### Densify quality profiles

| Profile | Speed | VRAM | Notes |
|---------|-------|------|-------|
| `turbo` | fastest | lowest | |
| `fast` | fast | low | default |
| `base` | balanced | medium | |
| `high` | slow | high | bidirectional matching |
| `precise` | slowest | heaviest | bidirectional, H_lr=800 |

## Platform support

| Tool | Windows x64 | Linux x64 | macOS arm64 |
|------|-------------|-----------|-------------|
| ffmpeg | ✅ auto | ✅ auto | ⚠️ `brew install ffmpeg` |
| COLMAP | ✅ auto (cuda/nocuda) | ⚠️ `apt install colmap` | ⚠️ `brew install colmap` |
| Brush | ✅ auto | ✅ auto | ✅ auto |
| densify | ✅ via uv+git | ✅ via uv+git | ✅ via uv+git |

## Notes

- Re-running `gaussify install` is safe — already-installed tools are skipped
- If fewer frames are registered than extracted, that's normal with sparse frame counts; use 200+ frames for best results
- The output directory is a valid COLMAP project — open it directly in LichtFeld Studio or other tools
