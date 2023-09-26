import json
import sys
from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from naapc import snd

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

    d = snd(raw)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = snd(d)
    assert d1.dict is d.dict
    assert d1.flatten_dict == d.flatten_dict

    d2 = snd(flatten)
    assert d2.dict == nested, get_dict_compare_msg(d2.dict, nested, indent=4, sort_keys=False)
    assert d2.flatten_dict == flatten, get_dict_compare_msg(
        d2.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = snd()
    assert d.dict == {}
    assert d.flatten_dict == {}
    assert d._d == {}

    d = snd({"raw": [raw, raw, snd(raw)]})
    assert d.dict == {"raw": [nested, nested, nested]}


def test_getitem():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))

    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)

    for p, v in flatten.items():
        assert d[p] == v

    with open(TEST_ASSET / "init_getitem.json", "r") as f:
        getitem_gt = json.load(f)

    for p, gt in getitem_gt.items():
        v = d[p]
        if isinstance(gt, dict):
            assert isinstance(v, snd)
            v = v.dict
        assert v == gt

    d.return_nested = False
    for p, gt in getitem_gt.items():
        v = d[p]
        if isinstance(gt, dict):
            assert isinstance(v, dict)
            v = v
        assert v == gt

    with pytest.raises(KeyError):
        a = d["not_exist_path"]


def test_delitem():
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    with open(TEST_ASSET / "init_del.json", "r") as f:
        del_gt = json.load(f)
    for p, gt in del_gt.items():
        d = snd(deepcopy(raw))
        del d[p]
        assert d.dict == gt["dict"]
        assert d.flatten_dict == gt["flatten"]

    with open(TEST_ASSET / "init_nested.json", "r") as f:
        nested = json.load(f)
    d = snd(deepcopy(raw))
    for k in nested.keys():
        del d[k]
    assert d.dict == {}
    assert d.flatten_dict == {}


def test_setitem():
    with open(TEST_ASSET / "init.json", "r") as f:
        raw = json.load(f)
    d = snd(raw)
    d["not_exist"] = {"something1": {"something2": 1}}
    assert d["not_exist;something1;something2"] == 1
    d["not_exist"] = {}
    assert "not_exist;something1;something2" not in d.flatten_dict

    d = snd(raw)
    d["not_exist"] = {"something1": {"something2": 1}}
    assert d["not_exist;something1;something2"] == 1
    d["not_exist;something1"] = 1
    assert "not_exist;something1;something2" not in d.flatten_dict

    d = snd()
    d["something"] = {}
    assert d.dict == {"something": {}}
    assert d.flatten_dict == {"something": {}}

    d = snd({"something": {}})
    assert d.dict == {"something": {}}
    assert d.flatten_dict == {"something": {}}
    d["something;node1"] = 1
    assert "something" not in d.flatten_dict
    d["something;node2"] = {}
    d["something;node2"] = {"something_else": 1}
    assert "something;node2" not in d.flatten_dict


def test_bool():
    d = snd()
    assert not d
    d["something"] = 1
    assert d
    del d["something"]
    assert not d


def test_paths():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))

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
    d = snd(raw)
    d.delimiter = "."
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = snd(d)
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    assert d1.dict == nested, get_dict_compare_msg(d1.dict, nested, indent=4, sort_keys=False)
    assert d1.flatten_dict == flatten, get_dict_compare_msg(
        d1.flatten_dict, flatten, indent=4, sort_keys=False
    )


def test_states():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
    d.delimiter = "+"
    states = d.states()
    d1 = snd().load_states(states)
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
        d = snd(json.load(f))
    with open(TEST_ASSET / "init_getitem.json", "r") as f:
        getitem_gt = json.load(f)

    for p, gt in getitem_gt.items():
        v = d.get(p)
        if isinstance(gt, dict):
            assert isinstance(v, snd)
            v = v.dict
        assert v == gt

    d.return_nested = False
    for p, gt in getitem_gt.items():
        v = d.get(p)
        if isinstance(gt, dict):
            assert isinstance(v, dict)
            v = v
        assert v == gt

    d.return_nested = True
    assert d.get("not_exist_path") is None
    assert d.get("not_exist_path", default=1) == 1
    assert d.get("not_exist_path;not_exist_path", default=1) == 1
    assert d.get("not_exist_path;not_exist_path") is None


def test_update_no_filting():
    d = snd()
    with open(TEST_ASSET / "init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(TEST_ASSET / "init_nested.json", "r") as f:
        nested = json.load(f)
    d.update(flatten)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = snd()
    d.update(snd(nested))
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d1 = snd(nested)
    d = snd()
    d.update(d1)
    assert d.dict == nested, get_dict_compare_msg(d.dict, nested, indent=4, sort_keys=False)
    assert d.flatten_dict == flatten, get_dict_compare_msg(
        d.flatten_dict, flatten, indent=4, sort_keys=False
    )

    d = snd(nested)
    update_dict = {
        "node1": 1.0,
        "nested;node2": "something",
        "not_exist": "here",
        "node2": None,
        "node7": {"double": {"trible": {"leave": 345, "not_exist": 555}}},
    }
    d.update(update_dict)
    with open(TEST_ASSET / "init_update1_gt_nested.json", "r") as f:
        nested_gt = json.load(f)
    with open(TEST_ASSET / "init_update1_gt_flatten.json", "r") as f:
        flatten_gt = json.load(f)
    assert d.dict == nested_gt
    assert d.flatten_dict == flatten_gt


def test_keys():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))

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
        d = snd(json.load(f))
    with open(TEST_ASSET / "values_depth1.json", "r") as f:
        gt = json.load(f)
    d.return_nested = False
    assert d.values() == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(), gt))
    with open(TEST_ASSET / "values_depth2.json", "r") as f:
        gt = json.load(f)
    assert d.values(2) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(2), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(2), gt))
    with open(TEST_ASSET / "values_depth3.json", "r") as f:
        gt = json.load(f)
    assert d.values(3) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(3), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(3), gt))
    with open(TEST_ASSET / "values_depth-1.json", "r") as f:
        gt = json.load(f)
    assert d.values(-1) == gt
    assert all(v1 == v2 for v1, v2 in zip(d.values(-1), gt))
    assert all(v2 == v1 for v1, v2 in zip(d.values(-1), gt))
    for v, v_gt in zip(d.values(-1), gt):
        if isinstance(v_gt, dict):
            assert isinstance(v_gt, snd)
    for v, v_gt in zip(d.values(-1), gt):
        if isinstance(v_gt, dict):
            assert isinstance(v_gt, dict)


def test_items():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
    with open(TEST_ASSET / "init_keys_depth1.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth1.json", "r") as f:
        v_gt = json.load(f)
    for i, (k, v) in enumerate(d.items()):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, snd)
            assert v.dict is d[k].dict
    d.return_nested = False
    for i, (k, v) in enumerate(d.items()):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k]

    with open(TEST_ASSET / "init_keys_depth2.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth2.json", "r") as f:
        v_gt = json.load(f)
    d.return_nested = True
    for i, (k, v) in enumerate(d.items(2)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, snd)
            assert v.dict is d[k].dict
    d.return_nested = False
    for i, (k, v) in enumerate(d.items(2)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k]

    with open(TEST_ASSET / "init_keys_depth3.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth3.json", "r") as f:
        v_gt = json.load(f)
    d.return_nested = True
    for i, (k, v) in enumerate(d.items(3)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, snd)
            assert v.dict is d[k].dict
    d.return_nested = False
    for i, (k, v) in enumerate(d.items(3)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert isinstance(v, dict)
            assert v is d[k]

    with open(TEST_ASSET / "init_keys_depth-1.json", "r") as f:
        k_gt = json.load(f)
    with open(TEST_ASSET / "values_depth-1.json", "r") as f:
        v_gt = json.load(f)
    d.return_nested = True
    for i, (k, v) in enumerate(d.items(-1)):
        assert k == k_gt[i]
        assert v == v_gt[i]
        if isinstance(v_gt[i], dict):
            assert isinstance(v, snd)
            assert v.dict is d[k].dict
    d.return_nested = False
    for i, (k, v) in enumerate(d.items(-1)):
        assert k_gt[i] == k
        assert v_gt[i] == v
        if isinstance(v_gt[i], dict):
            assert v is d[k]
            assert isinstance(v, dict)


def test_size():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
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
        d = snd(json.load(f))
    d1 = deepcopy(d)
    assert d == d1

    flatten = {p: v for p, v in reversed(d.flatten_dict.items())}
    d1 = snd(flatten)
    assert d == d1
    assert d == flatten

    d1["node1"] = "not exist"
    assert d != d1
    assert not d == d1

    d1 = snd(flatten)
    d1["Not exist"] = "null"
    assert d != d1
    assert not d == d1


def test_diff():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
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
        d = snd(json.load(f))
    assert len(d) == d.size()

    for k in d.keys():
        del d[k]
        assert len(d) == d.size()


def test_print():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
    assert str(d) == yaml.dump(d.dict, indent=2, sort_keys=False)
    assert d.json() == json.dumps(d.dict, sort_keys=False, indent=2)


def test_contain():
    with open(TEST_ASSET / "init.json", "r") as f:
        d = snd(json.load(f))
    assert "node1" in d
    assert "not exist" not in d
    d = snd()
    assert "node1" not in d
    assert "not exist" not in d


if __name__ == "__main__":
    # test_update_no_filting()
    # test_init()
    # test_getitem()
    # test_setitem()
    test_delitem()
    # test_bool()
    # test_paths()
    # test_set_delimiter()
    # test_states()
    # test_items()
    # test_eq()
    # test_get()
