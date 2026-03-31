"""
GPU backend detection — returns 'cuda', 'rocm', or 'cpu'.
"""
import shutil
import subprocess


def detect_gpu() -> str:
    if _has_cuda():
        return "cuda"
    if _has_rocm():
        return "rocm"
    return "cpu"


def _has_cuda() -> bool:
    return shutil.which("nvcc") is not None or _nvidia_smi_present()


def _nvidia_smi_present() -> bool:
    try:
        result = subprocess.run(
            ["nvidia-smi"], capture_output=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _has_rocm() -> bool:
    return shutil.which("rocminfo") is not None
