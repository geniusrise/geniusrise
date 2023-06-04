# node.py
from typing import Callable, List, Tuple, Any
from .types import Either
from .edge import Edge
import traceback
import inspect
import logging

log = logging.getLogger(__name__)


class Node:
    """
    Represents a node in the computation network.
    """

    def __init__(self, function: Callable[..., Any], name: str, edges: List[Tuple["Node", Edge]]) -> None:
        """
        Initializes the node with a function and a name.
        """
        self.function = function
        self.name = name
        # https://stackoverflow.com/questions/11040438/class-variables-is-shared-across-all-instances-in-python
        self.edges: List[Tuple["Node", Edge]] = edges

    def __repr__(self):
        """
        Returns a string representation of the node.
        """
        return f"Node({self.name})"

    def __add__(self, edge: Tuple["Node", Edge]) -> "Node":
        """
        Adds an edge to the node and returns the node at the end of the edge.
        This allows for chaining addition operations to construct a path through the computation network.
        """
        self.edges.append(edge)
        return edge[0]

    async def __call__(self, input: Any = None) -> Either:
        """
        Computes the function of the node and passes the result to the next nodes.
        """
        try:
            if inspect.iscoroutinefunction(self.function):
                if input is None:
                    result = await self.function()
                else:
                    result = await self.function(input)
            else:
                if input is None:
                    result = self.function()
                else:
                    result = self.function(input)
            for node, transform in self.edges:
                result = (await node(transform(result))).value
            return Either.ok(result)
        except Exception as e:
            traceback.print_exc()
            return Either.error(e)

    async def map(self, function: Callable[..., Any]) -> "Node":
        """
        Creates a new node that applies a function to the output of this node.
        """
        if inspect.iscoroutinefunction(self.function):

            async def new_function(x):
                return function(await self.function(x))

            return Node(new_function, self.name, self.edges)
        else:
            return Node(lambda x: function(self.function(x)), self.name, self.edges)

    async def reduce(self, function: Callable[..., Any], initial_value: Any) -> Any:
        """
        Applies a function to the output of this node and all its connected nodes, accumulating the results.
        """
        value = initial_value
        for node, transform in self.edges:
            if inspect.iscoroutinefunction(self.function):
                result = await self.function(initial_value)
            else:
                result = self.function(initial_value)

            either_result = await node(transform(result))
            value = function(value, either_result.value)
        return value
