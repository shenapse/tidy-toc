import os
import sys
from pathlib import Path

import pytest

sys.path.append(os.path.join("..", "scr"))

# from scr.collect_zip import check_parent_duplication, collect_zip
# from scr.Type_Alias import Path, Paths

from Type_Alias import Path, Paths

from collect_zip import collect_zip, get_non_unique_parent_dir

test_root: Path = Path(".")
dir_out: Path = test_root / "zip_out"
dir_in_ok: Path = test_root / "zip_in_ok"
dir_in_ng: Path = test_root / "zip_in_ng"
dir_in_ng2: Path = test_root / "zip_in_ng2"
N_dir: int = 10

# clean dir_out directory
def clean(dir: Path):
    if not dir.exists():
        dir.mkdir()
    else:

        def get_files(dir: Path) -> Paths:
            return list(dir.glob("**/*.zip"))

        files: Paths = get_files(dir)
        for f in files:
            f.unlink()
        assert len(get_files(dir)) == 0


def init_zip_dir_ok():
    # create dir_in_** if necessary
    if not dir_in_ok.exists():
        dir_in_ok.mkdir()
    for i in range(N_dir):
        dir: Path = Path(dir_in_ok / f"dir{i}")
        if not dir.exists():
            dir.mkdir()
        (dir / "z.zip").touch(exist_ok=True)
        (dir / "p.png").touch(exist_ok=True)
        (dir / "t.txt").touch(exist_ok=True)
        if i % 2 == 0:
            dir_nest: Path = Path(dir / f"dir_nest{i}")
            if not dir_nest.exists():
                dir_nest.mkdir()
            (dir_nest / "z.zip").touch(exist_ok=True)
            (dir_nest / "p.png").touch(exist_ok=True)
            (dir_nest / "t.txt").touch(exist_ok=True)


# NG case. more than one zip files in a dir
def init_zip_dir_ng():
    # create dir_in_** if necessary
    if not dir_in_ng.exists():
        dir_in_ng.mkdir()
    for i in range(10):
        dir: Path = Path(dir_in_ng / f"dir{i}")
        if not dir.exists():
            dir.mkdir()
        (dir / "z.zip").touch(exist_ok=True)
        if i % 2 == 0:
            (dir / "z_ng.zip").touch(exist_ok=True)
        (dir / "p.png").touch(exist_ok=True)
        (dir / "t.txt").touch(exist_ok=True)


# NG case: duplicated directory name
def init_zip_dir_ng2():
    # create dir_in_** if necessary
    if not dir_in_ng2.exists():
        dir_in_ng2.mkdir()
    for i in range(10):
        dir: Path = Path(dir_in_ng2 / f"dir{i}")
        if not dir.exists():
            dir.mkdir()
        (dir / "z.zip").touch(exist_ok=True)
        if i % 2 == 0 and i > 0:
            dir_nest: Path = dir / f"dir{i-1}"
            if not dir_nest.exists():
                dir_nest.mkdir()
                (dir_nest / "z_ng.zip").touch(exist_ok=True)


def get_zips_in_subdir(root: Path) -> Paths:
    return list(root.glob("**/*.zip"))


def test_prepare():
    clean(dir_out)
    clean(dir_in_ok)
    clean(dir_in_ng)
    init_zip_dir_ok()
    init_zip_dir_ng()
    init_zip_dir_ng2()


def test_check_dup_ok():
    zips: Paths = list(dir_in_ok.glob("**/*.zip"))
    assert len(get_non_unique_parent_dir(zips)) == 0


def test_collect_ok():
    n_zips: int = len(get_zips_in_subdir(dir_in_ok))
    zips: Paths = collect_zip(dir_in_ok, dir_out)
    assert len(zips) == n_zips


def test_collect_ng():
    with pytest.raises(Exception):
        collect_zip(dir_in_ng, dir_out)


def test_collect_ng2():
    with pytest.raises(Exception) as e:
        collect_zip(dir_in_ng2, dir_out)
