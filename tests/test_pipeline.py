from pathlib import Path
from unittest.mock import patch, call
from gaussify.pipeline import _extract_all


def test_frame_distribution_proportional(tmp_path):
    """Frames are distributed proportionally to video duration."""
    videos = [Path("short.mov"), Path("long.mov")]

    with patch("gaussify.pipeline.probe_duration", side_effect=[30.0, 90.0]), \
         patch("gaussify.pipeline.extract_frames") as mock_extract:

        _extract_all(videos, tmp_path / "frames", total_frames=200)

        calls = mock_extract.call_args_list
        assert len(calls) == 2
        # short (30s) → 25% → 50 frames; long (90s) → 75% → 150 frames
        _, kwargs0 = calls[0]
        _, kwargs1 = calls[1]
        assert calls[0][0][2] == 50   # count for short video
        assert calls[1][0][2] == 150  # count for long video


def test_frame_distribution_prefixes(tmp_path):
    """Each video gets a unique prefix to avoid filename collisions."""
    videos = [Path("a.mov"), Path("b.mov")]

    with patch("gaussify.pipeline.probe_duration", side_effect=[60.0, 60.0]), \
         patch("gaussify.pipeline.extract_frames") as mock_extract:

        _extract_all(videos, tmp_path / "frames", total_frames=100)

        assert mock_extract.call_args_list[0][1]["prefix"] == "v00_"
        assert mock_extract.call_args_list[1][1]["prefix"] == "v01_"


def test_frame_distribution_fallback_equal_split(tmp_path):
    """Falls back to equal split when duration cannot be probed."""
    videos = [Path("a.mov"), Path("b.mov"), Path("c.mov")]

    with patch("gaussify.pipeline.probe_duration", return_value=None), \
         patch("gaussify.pipeline.extract_frames") as mock_extract:

        _extract_all(videos, tmp_path / "frames", total_frames=90)

        counts = [c[0][2] for c in mock_extract.call_args_list]
        assert counts == [30, 30, 30]
