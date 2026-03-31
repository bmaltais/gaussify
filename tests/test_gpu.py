import subprocess
from gaussify.gpu import detect_gpu, _has_cuda, _has_rocm


def test_detect_gpu_cuda(mocker):
    mocker.patch("gaussify.gpu._has_cuda", return_value=True)
    mocker.patch("gaussify.gpu._has_rocm", return_value=False)
    assert detect_gpu() == "cuda"


def test_detect_gpu_rocm(mocker):
    mocker.patch("gaussify.gpu._has_cuda", return_value=False)
    mocker.patch("gaussify.gpu._has_rocm", return_value=True)
    assert detect_gpu() == "rocm"


def test_detect_gpu_cpu_fallback(mocker):
    mocker.patch("gaussify.gpu._has_cuda", return_value=False)
    mocker.patch("gaussify.gpu._has_rocm", return_value=False)
    assert detect_gpu() == "cpu"


def test_has_cuda_via_nvidia_smi(mocker):
    mocker.patch("shutil.which", return_value=None)
    mocker.patch(
        "subprocess.run",
        return_value=subprocess.CompletedProcess(args=[], returncode=0),
    )
    assert _has_cuda() is True


def test_has_cuda_missing(mocker):
    mocker.patch("shutil.which", return_value=None)
    mocker.patch("subprocess.run", side_effect=FileNotFoundError)
    assert _has_cuda() is False
