import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml

from naapc import ndict

ROOT = Path(__file__).resolve().parents[1]
TEST_SRC_DIR = ROOT / "test"
TEST_ASSET = TEST_SRC_DIR / "assets"
if str(TEST_SRC_DIR) not in sys.path:
    sys.path.append(str(TEST_SRC_DIR))

from utils import get_dict_compare_msg


def test_init():
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(TEST_ASSET / "init_nested.json", "r") as f:
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
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))

    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)

    for p, v in flatten.items():
        assert d[p] == v

    with open(TEST_ASSET / "init_getitem.json", "r") as f:
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
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    with open(TEST_ASSET / "init_del.json", "r") as f:
        del_gt = json.load(f)
    for p, gt in del_gt.items():
        d = ndict(deepcopy(raw))
        del d[p]
        assert d.dict == gt["dict"]
        assert d.flatten_dict == gt["flatten"]

    with open(TEST_ASSET / "init_nested.json", "r") as f:
        nested = json.load(f)
    d = ndict(deepcopy(raw))
    for k in nested.keys():
        del d[k]
    assert d.dict == {}
    assert d.flatten_dict == {}


def test_setitem():
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    d = ndict(raw)
    d["not_exist"] = {"something1": {"something2": 1}}
    assert d["not_exist;something1;something2"] == 1
    d["not_exist"] = {}
    assert "not_exist;something1;something2" not in d.flatten_dict

    d = ndict(raw)
    d["not_exist"] = {"something1": {"something2": 1}}
    assert d["not_exist;something1;something2"] == 1
    d["not_exist;something1"] = 1
    assert "not_exist;something1;something2" not in d.flatten_dict

    d = ndict()
    d["something"] = {}
    assert d.dict == {"something": {}}
    assert d.flatten_dict == {"something": {}}

    d = ndict({"something": {}})
    assert d.dict == {"something": {}}
    assert d.flatten_dict == {"something": {}}
    d["something;node1"] = 1
    assert "something" not in d.flatten_dict


def test_bool():
    d = ndict()
    assert not d
    d["something"] = 1
    assert d
    del d["something"]
    assert not d


def test_paths():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))

    with open(TEST_ASSET / "init_paths.json", "r") as f:
        paths = json.load(f)
    assert d.paths == paths


def test_set_delimiter():
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    with open(TEST_ASSET / "init_nested.json", "r") as f:
        nested = json.load(f)
    with open(TEST_ASSET / "delimiter_flatten.json", "r") as f:
        flatten = json.load(f)
    d = ndict(raw)
    d.delimiter = "."
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = ndict(d)
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    assert d1.dict == nested, get_dict_compare_msg(d1.dict, nested, indent=4, sort_keys=False)
    assert d1.flatten_dict == flatten, get_dict_compare_msg(
        d1.flatten_dict, flatten, indent=4, sort_keys=False
    )


def test_states():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    d.delimiter = "+"
    states = d.state_dict()
    d1 = ndict().load_state_dict(states)
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(TEST_ASSET / "init_nested.json", "r") as f:
        nested = json.load(f)
    assert d1.dict == nested, get_dict_compare_msg(d1.dict, nested, indent=4, sort_keys=False)
    assert d1.flatten_dict == flatten, get_dict_compare_msg(
        d1.flatten_dict, flatten, indent=4, sort_keys=False
    )


def test_get():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    with open(TEST_ASSET / "init_getitem.json", "r") as f:
        getitem_gt = json.load(f)

    for p, gt in getitem_gt.items():
        v = d.get(path=p)
        if isinstance(gt, dict):
            assert isinstance(v, ndict)
            v = v.dict
        assert v == gt

    for p, gt in getitem_gt.items():
        v = d.get(path=p, dict_as_ndict=False)
        if isinstance(gt, dict):
            assert isinstance(v, dict)
            v = v
        assert v == gt

    assert d.get("not_exist_path") is None
    assert d.get("not_exist_path", default=1) == 1
    assert d.get("not_exist_path;not_exist_path", default=1) == 1
    assert d.get("not_exist_path;not_exist_path") is None

    assert d.get(keys=["node1", "node2", ("node2", lambda tree, path: tree[path] + 1)]) == {
        "node1": "this",
        "node2": 2.0,
    }


def test_update_no_filting():
    d = ndict()
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(TEST_ASSET / "init_nested.json", "r") as f:
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
    update_dict = {
        "node1": 1.0,
        "nested;node2": "something",
        "not_exist": "here",
        "node2": None,
        "node7": {"double": {"trible": {"leave": 345, "not_exist": 555}}},
    }
    d.update(update_dict, ignore_missing=False, ignore_none=False)
    with open(TEST_ASSET / "init_update1_gt_nested.json", "r") as f:
        nested_gt = json.load(f)
    with open(TEST_ASSET / "init_update1_gt_flatten.json", "r") as f:
        flatten_gt = json.load(f)
    assert d.dict == nested_gt
    assert d.flatten_dict == flatten_gt


def test_update_filting():
    d = ndict()
    with open(TEST_ASSET / "init_update_no_none_gt_nested.json", "r") as f:
        nested = json.load(f)
    with open(TEST_ASSET / "init_update_no_none_gt_flatten.json", "r") as f:
        flatten = json.load(f)
    d.update(flatten, ignore_missing=False, ignore_none=True)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = ndict()
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    d.update(flatten, ignore_missing=True, ignore_none=False)
    assert d.dict == {}
    assert d.flatten_dict == {}


def test_keys():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))

    with open(TEST_ASSET / "init_keys_depth1.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys()) == set(gt)
    assert set(d.keys(1)) == set(gt)

    with open(TEST_ASSET / "init_keys_depth2.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys(2)) == set(gt)

    with open(TEST_ASSET / "init_keys_depth3.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys(3)) == set(gt)

    with open(TEST_ASSET / "init_keys_depth-1.json", "r") as f:
        gt = json.load(f)
    assert set(d.keys(-1)) == set(gt)
    assert set(d.keys(-1)) == set(d.flatten_dict.keys())


def test_values():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    with open(TEST_ASSET / "values_depth1.json", "r") as f:
        gt = json.load(f)
    assert d.values(1, dict_as_ndict=False) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(1, dict_as_ndict=True), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(1, dict_as_ndict=True), gt))
    with open(TEST_ASSET / "values_depth2.json", "r") as f:
        gt = json.load(f)
    assert d.values(2, dict_as_ndict=False) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(2, dict_as_ndict=True), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(2, dict_as_ndict=True), gt))
    with open(TEST_ASSET / "values_depth3.json", "r") as f:
        gt = json.load(f)
    assert d.values(3, dict_as_ndict=False) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(3, dict_as_ndict=True), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(3, dict_as_ndict=True), gt))
    with open(TEST_ASSET / "values_depth-1.json", "r") as f:
        gt = json.load(f)
    assert d.values(-1, dict_as_ndict=False) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(-1, dict_as_ndict=True), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(-1, dict_as_ndict=True), gt))
    for v, v_gt in zip(d.values(-1, dict_as_ndict=True), gt):
        if isinstance(v_gt, dict):
            assert isinstance(v_gt, ndict)
    for v, v_gt in zip(d.values(-1, dict_as_ndict=False), gt):
        if isinstance(v_gt, dict):
            assert isinstance(v_gt, dict)


def test_items():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    with open(TEST_ASSET / "init_keys_depth1.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth1.json", "r") as f:
        v_gt = json.load(f)
    for i, (k, v) in enumerate(d.items(1, dict_as_ndict=True)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, ndict)
            assert v.dict is d[k].dict
    for i, (k, v) in enumerate(d.items(1, dict_as_ndict=False)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k].dict

    with open(TEST_ASSET / "init_keys_depth2.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth2.json", "r") as f:
        v_gt = json.load(f)
    for i, (k, v) in enumerate(d.items(2)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, ndict)
            assert v.dict is d[k].dict
    for i, (k, v) in enumerate(d.items(2, dict_as_ndict=False)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k].dict

    with open(TEST_ASSET / "init_keys_depth3.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth3.json", "r") as f:
        v_gt = json.load(f)
    for i, (k, v) in enumerate(d.items(3)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, ndict)
            assert v.dict is d[k].dict
    for i, (k, v) in enumerate(d.items(3, dict_as_ndict=False)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k].dict

    with open(TEST_ASSET / "init_keys_depth-1.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth-1.json", "r") as f:
        v_gt = json.load(f)
    for i, (k, v) in enumerate(d.items(-1, dict_as_ndict=True)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, ndict)
            assert v.dict is d[k].dict
    for i, (k, v) in enumerate(d.items(-1, dict_as_ndict=False)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert v is d[k].dict
            assert isinstance(v, dict)


def test_size():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    assert d.size(ignore_none=False) == len(d.keys())
    assert d.size(2, ignore_none=False) == len(d.keys(2))
    assert d.size(3, ignore_none=False) == len(d.keys(3))
    assert d.size(-1, ignore_none=False) == len(d.keys(-1))

    assert d.size(ignore_none=True) == len(d.keys()) - 1
    assert d.size(2, ignore_none=True) == len(d.keys(2)) - 2
    assert d.size(3, ignore_none=True) == len(d.keys(3)) - 4
    assert d.size(-1, ignore_none=True) == len(d.keys(-1)) - 4

    size = d.size(ignore_none=False)
    for k in d.keys():
        del d[k]
        assert d.size(ignore_none=False) == size - 1
        size = d.size(ignore_none=False)


def test_eq():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    d1 = deepcopy(d)
    assert d == d1

    flatten = {p: v for p, v in reversed(d.flatten_dict.items())}
    d1 = ndict(flatten)
    assert d == d1
    assert d == flatten

    d1["node1"] = "not exist"
    assert d != d1
    assert not d == d1

    d1 = ndict(flatten)
    d1["Not exist"] = "null"
    assert d != d1
    assert not d == d1


def test_diff():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    d1 = deepcopy(d)
    assert d.diff(d1) == {} and isinstance(d.diff(d1), dict)
    d1["node"] = "not"
    assert d.diff(d1) == {"node": (None, "not")}
    assert d1.diff(d) == {"node": ("not", None)}
    d1["node1"] = "not"
    assert d.diff(d1) == {"node": (None, "not"), "node1": ("this", "not")}
    assert d1.diff(d) == {"node": ("not", None), "node1": ("not", "this")}


def test_len():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    assert len(d) == d.size()

    for k in d.keys():
        del d[k]
        assert len(d) == d.size()


def test_print():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    assert str(d) == yaml.dump(d.dict, indent=2, sort_keys=False)
    assert d.json_str() == json.dumps(d.dict, sort_keys=False, indent=2)


def test_contain():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = ndict(json.load(f))
    assert "node1" in d
    assert "not exist" not in d
    d = ndict()
    assert "node1" not in d
    assert "not exist" not in d


if __name__ == "__main__":
    # test_update_no_filting()
    test_setitem()
