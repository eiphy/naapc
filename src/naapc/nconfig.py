from copy import deepcopy
from pathlib import Path
from typing import Union

import yaml

from .ndict import NDict


class CustomArgs:
    def __init__(
        self,
        flag=None,
        atype=None,
        path=None,
        nargs=None,
        choices=None,
        default=None,
        isbool=False,
    ):
        self.flag = flag
        self.atype = atype
        self.path = path
        self.nargs = nargs
        self.choices = choices
        self.default = default
        self.isbool = isbool

    def __repr__(self):
        return f"{self.flag} {self.path}"


class NConfig(NDict):
    _arg_key = "_ARGUMENT_SPECIFICATION"
    reserved_keys = [_arg_key]
    allowable_types = [int, str, float, bool, type(None)]

    def __init__(self, config):
        config = deepcopy(config)
        if self._arg_key in config:
            self._arg_specification = config[self._arg_key]
            del config[self._arg_key]
        else:
            self._arg_specification = {}
        super(NConfig, self).__init__(config)
        self._check_types()

    def parse_update(self, parser, args):
        custom_args = []
        for path, v in self._flatten_dict.items():
            if isinstance(v, list):
                atype = type(v[0])
                nargs = "+"
            else:
                atype = type(v)
                nargs = None
            if isinstance(v, bool):
                isbool = True
                choices = [0, 1]
                atype = int
            else:
                isbool = False
                choices = None
            carg = {
                "flag": f"--{path.replace(';', '__')}",
                "isbool": isbool,
                "atype": atype,
                "path": path,
                "nargs": nargs,
                "choices": choices,
                "default": v,
            }

            spec = self._arg_specification.get(path, {})
            assert all(k != "atype" for k in spec.keys())
            carg.update(spec)
            custom_args.append(CustomArgs(**carg))

        for carg in custom_args:
            parser.add_argument(
                carg.flag,
                type=carg.atype,
                nargs=carg.nargs,
                choices=carg.choices,
                default=carg.default,
            )

        args, extra_args = parser.parse_known_args(args)
        for carg in custom_args:
            v = getattr(args, carg.flag.strip("-"))
            if v is not None:
                self[carg.path] = bool(v) if carg.isbool else v

        return extra_args

    ### setters & updators ###
    def update(self, d, ignore_missing_path=False):
        super(NConfig, self).update(d, ignore_missing_path)
        self._check_types()

    ### getters ###
    @property
    def str_configs(self):
        d = self.copy()
        for path, v in self._flatten_dict.items():
            d[path] = str(v)
        return d

    ### miscs ###
    def save(self, path):
        path = Path(path)
        path.parent.mkdir(exist_ok=True, parents=True)
        if self._arg_specification:
            d = {**self._d, self._arg_key: self._arg_specification}
        else:
            d = self._d
        with open(path, "w") as f:
            yaml.dump(d, f, indent=4, sort_keys=False)

    ### check ###
    def _check_type_v(self, v):
        return (
            all(any(isinstance(x, t) for t in self.allowable_types) for x in v)
            if isinstance(v, list)
            else any(isinstance(v, t) for t in self.allowable_types)
        )

    def _check_types(self):
        for path, v in self.flatten_dict.items():
            assert self._check_type_v(
                v
            ), f"Unexpected config value type of {path} {type(v)} / {self.allowable_types}"

    ### magics ###
    def __setitem__(self, path: str, value: Union[str, int, float, bool]):
        self._check_type_v(value)
        super(NConfig, self).__setitem__(path, value)
