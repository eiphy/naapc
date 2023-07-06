from typing import Any, Callable


def generate_depth_stop_condition(max_depth: int = -1) -> Callable:
    def depth_stop_condition(res: Any, node: Any, path: str, depth: int) -> bool:
        return max_depth != -1 and depth > max_depth

    return depth_stop_condition


def generate_subtree_stop_condition(subtree_path: str) -> Callable:
    def subtree_stop_condition(res: Any, node: Any, path: str, depth: int) -> bool:
        return path.startswith(subtree_path)

    return subtree_stop_condition
