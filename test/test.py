import argparse
import os
import sys
from copy import deepcopy
from pathlib import Path
from signal import raise_signal
from typing import Any

import yaml

sys.path.append(str(Path(__file__).parent.parent.absolute()))

from naapc import NConfig, NDict


class testNDict:
    def __init__(self):
        self.nd = NDict({"this": "is test"})
        self.test_copy()
        print("Pass copy test.")

        with open("test/config.yaml", "r") as f:
            self.rawd = yaml.safe_load(f)
        self.nd = NDict(self.rawd)
        self.test_init()
        print("Pass init test.")

        self.test_from_flatten_dict()
        print("Pass from flatten test.")

        self.test_paths()
        print("Pass paths test.")

        self.test_contains()
        print("Pass contains test.")

        self.test_eq()
        print("Pass eq test.")

        self.test_del()
        print("Pass del test.")

        self.test_getitem()
        print("Pass getitem test.")

        self.test_flatten()
        print("Pass flatten test.")

        self.test_setitem()
        print("Pass setitem test.")

        self.test_update()
        print("Pass update test.")

        self.test_compare()
        print("Pass compare test.")

    def test_init(self):
        nd1 = NDict(self.nd)
        assert nd1._d is self.nd._d
        assert nd1 == self.nd

        nd1 = NDict(deepcopy(self.nd._d))
        assert nd1 is not self.nd
        assert nd1 == self.nd
        del nd1["task;task"]
        self.nd["task;task"]
        assert nd1 != self.nd

    def test_from_flatten_dict(self):
        nd1 = NDict.from_flatten_dict(self.nd)
        assert nd1 is not self.nd
        assert nd1._d is not self.nd._d
        assert nd1 == self.nd

    def test_copy(self):
        assert self.nd.copy() is not self.nd
        assert self.nd.copy().flatten_dict == self.nd.flatten_dict

    def test_eq(self):
        nd = self.nd.copy()
        assert nd == self.nd
        nd["task;task"] = "not_exist"
        assert nd != self.nd
        nd = self.nd.copy()
        nd["not_exist"] = "not_exist"
        assert nd != self.nd

        d = deepcopy(self.nd.raw_dict)
        nd = NDict(d)
        assert nd == self.nd
        del d["task"]
        nd = NDict(d)
        assert nd != self.nd

    def test_paths(self):
        for p in self.nd.paths:
            self.nd[p]

        all_paths = []
        for path in self.nd.flatten_dict.keys():
            nodes = path.split(";")
            all_paths.extend(";".join(nodes[:i]) for i in range(1, len(nodes) + 1))
        assert set(self.nd.paths) == set(all_paths)

    def test_contains(self):
        for p in self.nd.paths:
            assert p in self.nd
            assert f"{p};fwejkl" not in self.nd

    def test_del(self):
        for path in self.nd.paths:
            nd = self.nd.copy()
            del nd[path]
            diff = set(self.nd.paths) - set(nd.paths)
            assert all(p.startswith(path) for p in diff)
            assert nd != self.nd

    def test_getitem(self):
        def _check(pks, k, v, nd):
            path = ";".join(pks + [k])
            assert nd[path] == v, f"Wong at {path}. raw: {v}, nd: {nd}"
            if isinstance(v, dict):
                for nk, nv in v.items():
                    _check(pks + [k], nk, nv, nd)

        for k, v in self.rawd.items():
            _check([], k, v, self.nd)

    def test_flatten(self):
        for path, v in self.nd.flatten_dict.items():
            assert (
                self.nd[path] == v
            ), f"Wrong at {path}. nd: {self.nd[path]}, flatten: {v}"

        def _check(pks, k, v, flatten):
            path = ";".join(pks + [k])
            if isinstance(v, dict):
                for nk, nv in v.items():
                    _check(pks + [k], nk, nv, flatten)
            else:
                assert (
                    flatten[path] == v
                ), f"Wrong at {path}. raw: {v}, flatten: {flatten[path]}"

        for k, v in self.rawd.items():
            _check([], k, v, self.nd.flatten_dict)

    def test_setitem(self):
        nd = self.nd.copy()
        for path in nd.flatten_dict.keys():
            nd[path] = 1

        assert nd != self.nd
        assert set(nd.paths) == set(self.nd.paths)
        for v in nd.flatten_dict.values():
            assert v == 1

        nd = self.nd.copy()
        nd["not_exist;not_exist;not_exist;not_exist"] = "not_exist"
        assert "not_exist" in nd
        assert "not_exist;not_exist" in nd
        assert "not_exist;not_exist;not_exist" in nd
        assert "not_exist;not_exist;not_exist;not_exist" in nd
        assert nd["not_exist;not_exist;not_exist;not_exist"] == "not_exist"

        assert nd != self.nd

    def test_update(self):
        nd = self.nd.copy()

        fd = {path: 1 for path in self.nd.flatten_dict.keys()}
        nd.update(fd)

        assert nd != self.nd
        assert set(nd.paths) == set(self.nd.paths)
        for v in nd.flatten_dict.values():
            assert v == 1

        nd1 = self.nd.copy()
        nd1.update(nd)
        assert nd1 != self.nd
        assert set(nd1.paths) == set(self.nd.paths)
        for v in nd1.flatten_dict.values():
            assert v == 1

        nd = self.nd.copy()
        fd = {"not_exist;not_exist;not_exist": "not_exist"}
        try:
            nd.update(fd)
            raise RuntimeError
        except Exception:
            pass
        nd.update(fd, ignore_missing_path=True)
        assert "not_exist" in nd
        assert "not_exist;not_exist" in nd
        assert "not_exist;not_exist;not_exist" in nd
        assert nd["not_exist;not_exist;not_exist"] == "not_exist"

        assert nd != self.nd

    def test_compare(self):
        nd = self.nd.copy()
        assert not nd.compare_dict(self.nd)
        assert not self.nd.compare_dict(nd)
        assert nd.compare_dict(self.nd) == self.nd.compare_dict(nd)

        diff1 = {}
        diff2 = {}
        for path, v in self.nd.flatten_dict.items():
            nd[path] = "not_exist"
            diff1[path] = ("not_exist", v)
            diff2[path] = (v, "not_exist")
            assert nd.compare_dict(self.nd) == diff1
            assert self.nd.compare_dict(nd) == diff2

        nd = self.nd.copy()
        diff1 = {}
        diff2 = {}
        for path, v in self.nd.flatten_dict.items():
            if v is None:
                continue
            del nd[path]
            diff1[path] = (None, v)
            diff2[path] = (v, None)
            assert nd.compare_dict(self.nd) == diff1
            assert self.nd.compare_dict(nd) == diff2

        nd = self.nd.copy()
        nd["not_exist;not_exist;not_exist"] = "not_exist"
        assert nd.compare_dict(self.nd) == {
            "not_exist;not_exist;not_exist": ("not_exist", None)
        }
        assert self.nd.compare_dict(nd) == {
            "not_exist;not_exist;not_exist": (None, "not_exist")
        }


class testNConfig:
    def __init__(self):
        with open("test/config.yaml", "r") as f:
            self.rawd = yaml.safe_load(f)
        self.nd = NDict(self.rawd)

        self.test_init()
        print("Pass init test.")

        self.test_parse()
        print("Pass arg parsing test.")

        with open("test/config_arg_spe.yaml", "r") as f:
            rawd_spe = yaml.safe_load(f)
        nd_spe = NDict(rawd_spe)

        self.config = NConfig(nd_spe)

        self.test_update()
        print("Pass update test.")

        self.test_setitem()
        print("Pass setitem test.")

        self.test_save()
        print("Pass save test.")

    def test_init(self):
        with open("test/config_arg_spe.yaml", "r") as f:
            rawd_spe = yaml.safe_load(f)
        nd_spe = NDict(rawd_spe)

        config = NConfig(self.rawd)
        assert config == self.nd
        assert config._d is not self.rawd

        config = NConfig(nd_spe)
        assert config != nd_spe
        assert config._arg_specification
        assert config._d is not self.rawd

    def test_parse(self):
        def _get_test_value(v):
            def _get(v):
                if isinstance(v, bool):
                    v = 0 if v else 1
                elif isinstance(v, float):
                    v = -1000
                elif isinstance(v, int):
                    v = -100
                elif isinstance(v, str):
                    v = "no_exist"
                elif isinstance(v, type(None)):
                    v = 1
                else:
                    raise ValueError(f"Unexpected type {type(v)}")
                return v

            if isinstance(v, list):
                _v = []
                for x in v:
                    _v.append(_get(x))
                return _v
            else:
                return _get(v)

        with open("test/config_arg_spe.yaml", "r") as f:
            rawd_spe = yaml.safe_load(f)
        nd_spe = NDict(rawd_spe)
        config = NConfig(nd_spe)
        for path, v in config.flatten_dict.items():
            config = NConfig(nd_spe)
            parser = argparse.ArgumentParser()
            if (
                path in config._arg_specification
                and "flag" in config._arg_specification[path]
            ):
                flag = config._arg_specification[path]["flag"]
            else:
                flag = f"--{path.replace(';', '__')}"
            if path == "data;dataset":
                args, extra_args = parser.parse_known_args([flag, "imagenet"])
            elif isinstance(v, list):
                args, extra_args = parser.parse_known_args(
                    [flag, *[str(x) for x in _get_test_value(v)]]
                )
            else:
                args, extra_args = parser.parse_known_args(
                    [flag, str(_get_test_value(v))]
                )
            extra_args = config.parse_update(parser, extra_args)
            assert len(extra_args) == 0
            if path == "data;dataset":
                assert config[path] == "imagenet"
            else:
                if isinstance(config[path], bool):
                    target = bool(_get_test_value(v))
                else:
                    target = _get_test_value(v)
                assert config[path] == target
            _nd_spe = nd_spe.copy()
            del _nd_spe["_ARGUMENT_SPECIFICATION"]
            for _path, _v in _nd_spe.flatten_dict.items():
                if _path != path:
                    assert config[_path] == _v
                else:
                    assert config[_path] != _v

    def test_update(self):
        config = self.config.copy()

        fd = {path: 1 for path in self.config.flatten_dict.keys()}
        config.update(fd)

        assert config != self.config
        assert set(config.paths) == set(self.config.paths)
        for v in config.flatten_dict.values():
            assert v == 1

        config1 = self.config.copy()
        config1.update(config)
        assert config1 != self.config
        assert set(config1.paths) == set(self.config.paths)
        for v in config1.flatten_dict.values():
            assert v == 1

        config = self.config.copy()
        fd = {"not_exist;not_exist;not_exist": "not_exist"}
        try:
            config.update(fd)
            raise RuntimeError
        except Exception:
            pass
        config.update(fd, ignore_missing_path=True)
        assert "not_exist" in config
        assert "not_exist;not_exist" in config
        assert "not_exist;not_exist;not_exist" in config
        assert config["not_exist;not_exist;not_exist"] == "not_exist"

        assert config != self.config

        try:
            config.update({"task;task": {"1": 1}})
            raise RuntimeError
        except Exception:
            pass

    def test_setitem(self):
        config = self.config.copy()
        for path in config.flatten_dict.keys():
            config[path] = 1

        assert config != self.config
        assert set(config.paths) == set(self.config.paths)
        for v in config.flatten_dict.values():
            assert v == 1

        config = self.config.copy()
        config["not_exist;not_exist;not_exist;not_exist"] = "not_exist"
        assert "not_exist" in config
        assert "not_exist;not_exist" in config
        assert "not_exist;not_exist;not_exist" in config
        assert "not_exist;not_exist;not_exist;not_exist" in config
        assert config["not_exist;not_exist;not_exist;not_exist"] == "not_exist"

        assert config != self.config

        try:
            config["task;task"] = {1: 1}
            raise ValueError
        except Exception:
            pass

    def test_save(self):
        self.config.save("tmp.yaml")
        with open("tmp.yaml", "r") as f:
            d = yaml.safe_load(f)
        config = NConfig(d)
        assert config == self.config
        assert config._arg_specification == self.config._arg_specification
        os.system("rm -rf tmp.yaml")


testNDict()

testNConfig()
