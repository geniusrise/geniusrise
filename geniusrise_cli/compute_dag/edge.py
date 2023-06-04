from typing import Callable, Any

# Define Edge as a type alias for a Callable
Edge = Callable[[Any], Any]


# Define a no-op function to use as a default edge
def noop(x: Any) -> Any:
    return x
