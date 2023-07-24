import json

with open("test/init_paths.json", "r") as f:
    paths = json.load(f)
with open("test/init_nested.json", "r") as f:
    nested = json.load(f)
with open("test/init_flatten.json", "r") as f:
    flatten = json.load(f)

res = {p: {"dict": nested, "flatten": flatten} for p in paths}

with open("test/init_del.json", "w") as f:
    json.dump(res, f, sort_keys=False, indent=4)
