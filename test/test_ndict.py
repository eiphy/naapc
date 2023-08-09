import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest

from naapc import ndict

ROOT = Path(__file__).resolve().parents[1]
TEST_SRC_DIR = ROOT / "test"
if str(TEST_SRC_DIR) not in sys.path:
    sys.path.append(str(TEST_SRC_DIR))

from utils import get_dict_compare_msg


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

    d2 = ndict(flatten)
    assert d2.dict == nested, get_dict_compare_msg(d2.dict, nested, indent=4, sort_keys=False)
    assert d2.flatten_dict == flatten, get_dict_compare_msg(
        d2.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = ndict()
    assert d.dict == {}
    assert d.flatten_dict == {}
    assert d._d == {}
    assert d._flatten_dict == {}

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

def test_delitem():
    with open(ROOT / "test/init.json", "r") as f:
        raw = json.load(f)
    with open(ROOT / "test/init_del.json", "r") as f:
        del_gt = json.load(f)
    for p, gt in del_gt.items():
        d = ndict(deepcopy(raw))
        del d[p]
        assert d.dict == gt["dict"]
        assert d.flatten_dict == gt["flatten"]

    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)
    d = ndict(deepcopy(raw))
    for k in nested.keys():
        del d[k]
    assert d.dict == {}
    assert d.flatten_dict == {}


def test_paths():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))

    with open(ROOT / "test/init_paths.json", "r") as f:
        paths = json.load(f)
    assert d.paths == paths

def test_set_delimiter():
    with open(ROOT / "test/init.json", "r") as f:
        raw = json.load(f)
    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)
    with open(ROOT / "test/delimiter_flatten.json", "r") as f:
        flatten = json.load(f)
    d = ndict(raw)
    d.delimiter = "."
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = ndict(d)
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    assert d1.dict == nested, get_dict_compare_msg(d1.dict, nested, indent=4, sort_keys=False)
    assert d1.flatten_dict == flatten, get_dict_compare_msg(
        d1.flatten_dict, flatten, indent=4, sort_keys=False
    )

def test_states():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))
    d.delimiter = "+"
    states = d.state_dict()
    d1 = ndict().load_state_dict(states)
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)
    assert d1.dict == nested, get_dict_compare_msg(d1.dict, nested, indent=4, sort_keys=False)
    assert d1.flatten_dict == flatten, get_dict_compare_msg(
        d1.flatten_dict, flatten, indent=4, sort_keys=False
    )

def test_get():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))
    with open(ROOT / "test/init_getitem.json", "r") as f:
        getitem_gt = json.load(f)

    for p, gt in getitem_gt.items():
        v = d.get(path=p)
        if isinstance(gt, dict):
            assert isinstance(v, ndict)
            v = v.dict
        assert v == gt
    
    assert d.get("not_exist_path") is None
    assert d.get("not_exist_path", default=1)  == 1
    assert d.get("not_exist_path;not_exist_path", default=1)  == 1
    assert d.get("not_exist_path;not_exist_path")  is None

    assert d.get(keys=["node1", "node2", ("node2", lambda tree, path: tree[path] + 1)]) == {"node1": "this", "node2": 2.0}

def test_update_no_filting():
    d = ndict()
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)
    d.update(flatten, ignore_missing=False, ignore_none=False)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = ndict()
    d.update(nested, ignore_missing=False, ignore_none=False)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = ndict(nested)
    d = ndict()
    d.update(d1, ignore_missing=False, ignore_none=False)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = ndict(nested)
    update_dict = {"node1": 1.0, "nested;node2": "something", "not_exist": "here", "node2": None, "node7": {"double": {"trible": {"leave": 345, "not_exist": 555}}}}
    d.update(update_dict, ignore_missing=False, ignore_none=False)
    with open(ROOT / "test/init_update1_gt_nested.json", "r") as f:
        nested_gt = json.load(f)
    with open(ROOT / "test/init_update1_gt_flatten.json", "r") as f:
        flatten_gt = json.load(f)
    assert d.dict == nested_gt
    assert d.flatten_dict == flatten_gt

def test_update_filting():
    d = ndict()
    with open(ROOT / "test/init_update_no_none_gt_nested.json", "r") as f:
        nested = json.load(f)
    with open(ROOT / "test/init_update_no_none_gt_flatten.json", "r") as f:
        flatten = json.load(f)
    d.update(flatten, ignore_missing=False, ignore_none=True)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = ndict()
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    d.update(flatten, ignore_missing=True, ignore_none=False)
    assert d.dict == {}
    assert d.flatten_dict == {}

def test_keys():
    with open(ROOT / "test/init.json", "r") as f:
        d = ndict(json.load(f))

    with open(ROOT / "test/init_keys_depth1.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys()) == set(gt)
    assert set(d.keys(1)) == set(gt)

    with open(ROOT / "test/init_keys_depth2.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys(2)) == set(gt)

    with open(ROOT / "test/init_keys_depth3.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys(3)) == set(gt)

    with open(ROOT / "test/init_paths.json", "r") as f:
        paths = json.load(f)
    assert d.keys(-1) == paths

if __name__ == "__main__":
    test_keys()
