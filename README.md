# Nested Automated Argument Parsing Configuration (NAAPC)
NAAPC contains two classes: NConfig and NDict.
NDict provides method to easily manipulate nested dictionaries.
NConfig is a subclass of NDict and can **automatically modify configurations according to CLI arguments**.

## Typical Usage.
Assume a configuration file test.yaml:
```yaml
task:
  task: classification
train:
  pretrain: false
  loss_args:
    lr: 0.1
```
The typical usage is as follows:
```python
from naapc import NConfig
from argparse import parser

parser.add_argument("-c", type=str, dest="config")
args, extra_args = parser.parse_known_args(["-c", "test.yaml", "--task;task", "regression", "--train;loss_args;lr", "0.2", "--train;pretrain", "1", "--others", "other"])

with open(args.config, "r") as f:
  raw = yaml.safe_load(f)
config = NConfig(raw)
extra_args = config.parse_update(parser, extra_args)
```
The resulting configurations:
```yaml
task:
  task: regression
train:
  pretrain: true
  loss_args:
    lr: 0.2
```

The data type is determined by the type in the configuration file.
The boolean data is treated as integer number 1 and 0 during parsing.

You may custom the arguments:
```yaml
task:
  task: regression
train:
  pretrain: true
  loss_args:
    lr: 0.2
_ARGUMENT_SPECIFICATION:
  task;task:
    flag: --task
    choices: ["regression", "classification"]
  train;lr:
    flag: lr
```

## NDict Usages
for a sample configuration test.yaml file:
```yaml
task:
  task: classification
train:
  loss_args:
    lr: 0.1
```

```python
from naapc import NDict

with open("test.yaml", "r") as f:
  raw = yaml.safe_load(f)
nd = NDict(raw)

nd1 = NDict.from_flatten_dict(nd.flatten_dict) # nd1 == nd
"task;path" in nd                      # "task" in raw and "path" in raw["task"]
del nd["task;path"]                    # del raw["task]["path]
nd["task;path"] = "cwd"                # raw["task"]["path"] = Path(".").absolute()
nd.flatten_dict                        # {"task;task": "classification", "train;loss_args;lr": 0.1}
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
nd1 = nd.copy()                        # nd1 = deepcopy(nd)
nd1 == nd                              # nd1.flatten_dict == nd.flatten_dict
nd1["task;path"] = "xcwd"
nd1["task;extra"] = "ecwd"
nd["train;epochs"] = 100
nd.compare_dict(nd1)                   # {"task;path": ("cwd", "xcwd"), "task;extra": (None, ecwd), "train;epochs": (100, None)}
```

## NConfig Usage
NConfig only supports int, str, float, bool, and list of these types.
The NConfig automatically checks data type when modifications are applied.
Note that argument specification ("_ARGUMENT_SPECIFICATION") does not count as part of the configurations but will be saved when use save() method.

```python
config.save("path.yaml")               # Save configurations as a yaml file
```

Other functionalities are the same to NDict.
