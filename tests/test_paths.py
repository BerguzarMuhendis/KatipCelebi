from pathlib import Path

from shared.paths import assets_dir


def test_assets_dir_returns_path():
    p = assets_dir()
    assert isinstance(p, Path)
