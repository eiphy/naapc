from naapc import ndict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# TODO Test "" key.
def dict_like_test():
    with open(ROOT / "test/init.json", "r") as f:
        raw = json.load(f)
    with open(ROOT / "test/init_flatten.json", "r") as f:
        flatten = json.load(f)
    with open(ROOT / "test/init_nested.json", "r") as f:
        nested = json.load(f)

    d = ndict(raw)
    assert d.flatten_dict == flatten
    assert d.dict == nested


if __name__ == "__main__":
    dict_like_test()
