# Nested Automated Argument Parsing Configuration (NAAPC)
[NAAPC](https://pypi.org/project/naapc/) contains two classes: NConfig and NDict.
NDict provides method to easily manipulate nested dictionaries.
NConfig is a subclass of NDict and can **automatically modify configurations according to CLI arguments**.

## Installation
```bash
pip install naapc
```

Or from source code:
```bash
pip install .
```

## Typical Usage.
## ndict Usages
for a sample configuration test.yaml file:
```yaml
task:
  task: classification
train:
  loss_args:
    lr: 0.1
```
and a sample list configuration test_list.yaml file:
```yaml
l:
- d:
    task:
      task: classification
- d:
    train:
      loss_args:
        lr: 0.1
```

```python
from naapc import ndict

with open("test.yaml", "r") as f:
  raw = yaml.safe_load(f)
nd = ndict(raw["d"], delimiter=";")
nd1 = ndict.from_flatten_dict(nd.flatten_dict) # nd1 == nd
nd2 = ndict.from_list_of_dict(raw["l"]) # nd2 == nd1 == nd

"task;path" in nd                      # "task" in raw and "path" in raw["task"]
del nd["task;path"]                    # del raw["task]["path]
nd["task;path"] = "cwd"                # raw["task"]["path"] = Path(".").absolute()
nd.flatten_dict                        # {"task;task": "classification", "train;loss_args;lr": 0.1}
nd.flatten_dict_split                  # raw["l"]
nd.paths                               # ["task", "task;task", "train", "train;loss_args", "train;loss_args;lr"]
nd.get("task;seed", 1)                 # raw["task"].get("seed", 1)
nd.raw_dict                            # raw
nd.size                                # len(nd.flatten_dict)
nd.update({"task;here": "there"})      # raw["task]["here] = "there
nd.items()                             # raw.items()
nd.keys()                              # raw.keys()
nd.values()                            # raw.values()
len(nd)                                # len(raw)
bool(nd)                               # len(nd) > 0
nd1 == nd                              # nd1.flatten_dict == nd.flatten_dict
nd1["task;path"] = "xcwd"
nd1["task;extra"] = "ecwd"
nd["train;epochs"] = 100
nd.diff(nd1)                   # {"task;path": ("cwd", "xcwd"), "task;extra": (None, ecwd), "train;epochs": (100, None)}
```

Check test/test_ndict.py for detailed usage.

## Typing
Add a type
```python
NestedOrDict = Union[ndict, dict]
```
