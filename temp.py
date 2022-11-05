import yaml

from naapc import NDict

with open("sample.yaml", "r") as f:
    raw = yaml.safe_load(f)
a = NDict(raw)
raw["l"] = a.flatten_dict_split
with open("sample.yaml", "w") as f:
    yaml.safe_dump(raw, f, sort_keys=False)
