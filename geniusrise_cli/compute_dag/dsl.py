from pyparsing import Word, alphas, alphanums, Literal, Group, OneOrMore
import inspect
import logging
from .node import Node
from .edge import Edge, noop

log = logging.getLogger(__file__)

# DSL syntax
identifier = Word(alphas, alphanums + "_")
transformTo = Literal("]->")
toTransform = Literal("-[")
transform = Group(toTransform + identifier + transformTo)
pipeline = Group(identifier + OneOrMore(transform + identifier))


# Define a function to construct a Node from a string
def construct_node(s, functions) -> Node:
    function = functions.get(s)
    if function is None or not inspect.isfunction(function):
        raise ValueError(f"No function named '{s}' found in the global scope")
    return Node(function, s, [])


# Define a function to construct an Edge from a string
def construct_edge(s, functions) -> Edge:
    if s == "noop":
        return noop
    function = functions.get(s)
    if function is None or not inspect.isfunction(function):
        raise ValueError(f"No function named '{s}' found in the global scope")
    else:
        return function


# Define a function to parse a pipeline
def parse_pipeline(s, functions):
    result = pipeline.parseString(s)
    log.info(f"Successfully parsed pipeline: {result}")

    nodes = {name: construct_node(name, functions) for name in result[0][::2]}

    for i in range(0, len(result[0]) - 1, 2):
        node1 = nodes[result[0][i]]
        transform = construct_edge(result[0][i + 1][1], functions)
        node2 = nodes[result[0][i + 2]]
        node1 + (node2, transform)
        log.info(f"Connecting pipeline: {''.join([str(node1), '-[', str(transform.__name__), ']->', str(node2)])}")

    # return the first node in the pipeline
    start_node = nodes[result[0][0]]
    # network = start_node.reduce(lambda m, x: m + f" -> {str(x)}", "")
    # log.error(network)
    return start_node
