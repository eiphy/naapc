import argparse
from copy import deepcopy
from pathlib import Path
from typing import Union

import yaml

from .ndict import NDict, NestedOrDict


class CustomArgs:
    def __init__(
        self,
        flag: str = None,
        atype=None,
        path: str = None,
        nargs: str = None,
        choices: list = None,
        default=None,
        isbool: bool = False,
    ) -> None:
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
    """Nested configuration based on NDict class.
    You are not supposed to modify the data outside this class!
    """

    _arg_key = "_ARGUMENT_SPECIFICATION"
    _ignore_key = "_IGNORE_IN_CLI"
    reserved_keys = [_arg_key, _ignore_key]

    # List is also allowed.
    allowable_types = [int, str, float, bool, type(None)]

    def __init__(self, config: NestedOrDict, delimiter: str = ";") -> None:
        # Configuration is supposed to be read-only. Therefore should not be modified in outside.
        config = deepcopy(config)
        if self._arg_key in config:
            self._arg_specification = config[self._arg_key]
            del config[self._arg_key]
        else:
            self._arg_specification = {}
        super(NConfig, self).__init__(config, delimiter=delimiter)
        self._check_types()

    @property
    def raw_dict(self):
        return deepcopy(self._d)

    @property
    def flatten_dict(self):
        return deepcopy(self._flatten_dict)

    @property
    def flatten_dict_split(self):
        return deepcopy(
            [NDict.from_flatten_dict({p: v}).raw_dict for p, v in self.flatten_dict.items()]
        )

    @property
    def paths(self):
        return deepcopy(self._paths)

    def _get_custom_args(self) -> list[CustomArgs]:
        """Generate customized arguments."""
        custom_args = []
        for path, v in self._flatten_dict.items():
            spec = self._arg_specification.get(path, {})
            if spec == self._ignore_key:
                continue
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
                "flag": f"--{path.replace(self.delimiter, '__')}",
                "isbool": isbool,
                "atype": atype,
                "path": path,
                "nargs": nargs,
                "choices": choices,
                "default": v,
            }

            assert all(k != "atype" for k in spec.keys())
            carg.update(spec)
            custom_args.append(CustomArgs(**carg))

        return custom_args

    def add_to_argparse(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """Add arguments to parser.
        For a path "task;task", the argument is specified as "--task__task".
        The type is inferred from the configuration file.
        Use integer 1 and 0 for boolean values.
        For list, nargs are automatically configured.

        The flag, type, and other options can be customized. See README.md.
        Use "_IGNORE_IN_CLI" to omit the path when adding to parse.
        """
        custom_args = self._get_custom_args()
        for carg in custom_args:
            parser.add_argument(
                carg.flag,
                type=carg.atype,
                nargs=carg.nargs,
                choices=carg.choices,
                default=carg.default,
            )
        return parser

    def parse_update(self, parser, args) -> list:
        """Parse CLI arguments and update the configurations accordingly."""
        custom_args = self._get_custom_args()

        args, extra_args = parser.parse_known_args(args)
        for carg in custom_args:
            v = getattr(args, carg.flag.strip("-"))
            if v is not None:
                self[carg.path] = bool(v) if carg.isbool else v

        return extra_args

    ### getters ###
    @property
    def str_configs(self) -> "NConfig":
        """Return NConfig object with every value in string."""
        d = deepcopy(self)
        for path, v in self._flatten_dict.items():
            d[path] = str(v)
        return d

    ### miscs ###
    def save(self, path: Union[Path, str]) -> None:
        """Save the configuraion. CLI specification will also be saved."""
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
        """Check the data type for a single value. The allowaed dtype is stated
        in self.allowable_types.
        """
        return (
            all(any(isinstance(x, t) for t in self.allowable_types) for x in v)
            if isinstance(v, list)
            else any(isinstance(v, t) for t in self.allowable_types)
        )

    def _check_types(self):
        """Check the data type. Call _check_type_v on each entry."""
        for path, v in self.flatten_dict.items():
            assert self._check_type_v(
                v
            ), f"Unexpected config value type of {path} {type(v)} / {self.allowable_types}"

    ### magics ###
    def __setitem__(self, path: str, value: Union[str, int, float, bool]):
        """Same to NDict but do type checking."""
        self._check_type_v(value)
        super(NConfig, self).__setitem__(path, value)
