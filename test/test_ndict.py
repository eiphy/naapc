import json
import sys
from pathlib import Path

import pytest

from naapc import ndict

ROOT = Path(__file__).resolve().parents[1]
TEST_SRC_DIR = ROOT / "test"
if str(TEST_SRC_DIR) not in sys.path:
    sys.path.append(str(TEST_SRC_DIR))

from utils import get_dict_compare_msg


# TODO Test "" key.
def test_init():
    with open(ROOT / "test/init.json", "r") as f:
        raw = json.load(f)
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)

    d = ndict(raw)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = ndict(d)
    assert d1.dict is d.dict
    assert d1.flatten_dict is d.flatten_dict


def test_paths():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))

    with open(ROOT / "test/init_paths.json", "r") as f:
        paths = json.load(f)
    assert d.paths == paths


def test_getitem():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))

    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)

    for p, v in flatten.items():
        assert d[p] == v

    with open(ROOT / "test/init_getitem.json", "r") as f:
        getitem_gt = json.load(f)

    for p, gt in getitem_gt.items():
        v = d[p]
        if isinstance(gt, dict):
            assert isinstance(v, ndict)
            v = v.dict
        assert v == gt

    with pytest.raises(KeyError):
        a = d["not_exist_path"]


if __name__ == "__main__":
    test_getitem()