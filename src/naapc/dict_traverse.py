from typing import Any, Callable, Optional, Union

from .stop_conditions import generate_depth_stop_condition


### Algs ###
def dfs(
    tree: dict,
    res: Any,
    node: Any,
    path: str,
    depth: int,
    action: Callable,
    stop_condition: Callable,
) -> Any:
    """Depth-first traverse.

    Args:
        tree (Any): The whole dictionary. This argument is used to provide global information and
            modify the tree.
        res (Any): Current results.
        node (Any): Current node (value).
        path (str): Current path (key)
        depth (int): Current depth (0 at root)
        action (callable): Action.
        stop_condition (callable): Whether should stop the traverse process.

    Returns:
        Any: Results
    """
    if stop_condition(res, node, path, depth):
        return res

    action(tree, res, node, path, depth)

    if isinstance(node, dict):
        for k, v in node.items():
            next_path = k if path is None else ";".join([path, k])
            dfs(tree, res, v, next_path, depth + 1, action, stop_condition)
    else:
        return res


def traverse(
    tree: dict,
    res: Any,
    actions: Union[Callable, tuple[Callable, dict[str, Callable]]],
    depth: int = -1,
    stop_condition: Optional[Union[list[Callable], Callable]] = None,
    alg: Callable = dfs,
) -> Any:
    """Go through nodes in the tree and apply actions / collect data.

    Args:
        res (Any): Where the final results will be.
        actions (Union[callable, tuple[callable, dict[str, callable]]]): action applied on all nodes or A tuple of
            (default action, {path: path actions}). Each callable should accept: tree, res, node, path, depth 5
            arguments. If the dictionary is modified, the action function must also update the flatten dictionary at
            the same time.
        depth (Optional[int], optional): Maximum traverse depth. Defaults to -1, which means traverse all depth.
        stop_condition (Optional[Union[list[callable], callable]], optional): Callable which returns bool to
            determine whether the tranverse should be stopped. This callable should accept res, node, path, depth 4
            arguments. It can also be a list of callables. In that case all the callable must return True to stop
            the traverse process. Defaults to None which means no extra conditions other depth.
        alg (callable, optional): Algorithm used to traverse the tree. Currently only support dfs. It should accept
            res, node, path, depth, actions and stop_condition 6 arguments. Defaults to dfs.

    Returns:
        Any: The results
    """
    action = _generate_action_pipeline(actions)
    stop_condition = _generate_stop_condition_pipeline(stop_condition, depth)

    return alg(tree, res, tree, None, 0, action, stop_condition)


def _generate_action_pipeline(
    actions: Union[Callable, tuple[Callable, dict[str, Callable]]]
) -> Callable:
    if isinstance(actions, tuple):
        default_action = actions[0]
        if len(actions) == 2:
            specific_actions = actions[1]
    else:
        default_action = actions
        specific_actions = {}

    def action_pipeline(tree: Any, res: Any, node: Any, path: str, depth: int) -> None:
        if path in specific_actions:  # type: ignore
            specific_actions[path](tree, res, node, path, depth)  # type: ignore
        else:
            default_action(tree, res, node, path, depth)

    return action_pipeline


def _generate_stop_condition_pipeline(
    conditions: Optional[Union[list[Callable], Callable]], max_depth: int = -1
) -> Callable:
    conditions = [conditions] if isinstance(conditions, Callable) else conditions
    conditions = [] if conditions is None else conditions
    conditions.append(generate_depth_stop_condition(max_depth))

    def stop_condition_pipeline(res: Any, node: Any, path: str, depth: int) -> bool:
        for cond in conditions:
            if cond(res, node, path, depth):
                return True
        return False

    return stop_condition_pipeline
