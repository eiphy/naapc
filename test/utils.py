import json
from naapc import NestedOrDict


def get_dict_compare_msg(d1: dict, d2: dict, **kwargs) -> str:
    return f"{json.dumps(d1, **kwargs)}\n\n--------------------{json.dumps(d2, **kwargs)}"
