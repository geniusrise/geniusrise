# import time
# import logging
# import yaml  # type: ignore
# import importlib
# from functools import lru_cache
# from typing import Callable, Dict, Any, List
# from geniusrise.functions.base import FunctionWrapper

# log = logging.getLogger(__file__)


# class Node(FunctionWrapper):
#     """
#     A Node in the graph, which wraps a function and its input/output schemas.
#     """

#     def __init__(self, func: Callable):
#         super().__init__(func)
#         self.incoming_edges = []
#         self.outgoing_edges = []

#     @lru_cache(maxsize=None)
#     def __call__(self, *args, **kwargs) -> Any:
#         """
#         Call the underlying function with the given arguments.
#         """
#         try:
#             start_time = time.time()
#             result = super().__call__(*args, **kwargs)
#             end_time = time.time()
#             log.info(f"Node {self.get_function_name()} executed in {end_time - start_time} seconds")
#             return result
#         except Exception as e:
#             log.error(f"Error executing node {self.get_function_name()}: {e}")
#             raise

#     def to_dict(self) -> Dict[str, str]:
#         """
#         Convert the Node to a dictionary for serialization.
#         """
#         return {
#             "module": self.func.__module__,
#             "function": self.func.__qualname__,
#         }

#     @staticmethod
#     def from_dict(d: Dict[str, str]) -> "Node":
#         """
#         Create a Node from a dictionary.
#         """
#         module = importlib.import_module(d["module"])
#         func = getattr(module, d["function"])
#         return Node(func)


# class Edge:
#     """
#     An Edge in the graph, which represents a dependency between two Nodes.
#     """

#     def __init__(self, source: Node, target: Node):
#         self.source = source
#         self.target = target
#         source.outgoing_edges.append(self)
#         target.incoming_edges.append(self)

#     def to_dict(self) -> Dict[str, str]:
#         """
#         Convert the Edge to a dictionary for serialization.
#         """
#         return {
#             "source": self.source.get_function_name(),
#             "target": self.target.get_function_name(),
#         }

#     @staticmethod
#     def from_dict(d: Dict[str, str], nodes: List[Node]) -> "Edge":
#         """
#         Create an Edge from a dictionary.
#         """
#         source = next(node for node in nodes if node.get_function_name() == d["source"])
#         target = next(node for node in nodes if node.get_function_name() == d["target"])
#         return Edge(source, target)


# class Graph:
#     """
#     A Graph, which represents a set of Nodes and Edges.
#     """

#     def __init__(self):
#         self.nodes = []
#         self.edges = []

#     def add_node(self, func: Callable) -> Node:
#         """
#         Add a Node to the graph.
#         """
#         node = Node(func)
#         self.nodes.append(node)
#         return node

#     def add_edge(self, source: Node, target: Node):
#         """
#         Add an Edge to the graph.
#         """
#         # Check that the output type of 'source' matches the input type of 'target'
#         source_output_type = source.get_output_schema().return_value.annotation
#         target_input_type = next(iter(target.get_input_schema().__annotations__.values()))
#         if source_output_type != target_input_type:
#             raise TypeError("The output type of the source node does not match the input type of the target node")

#         edge = Edge(source, target)
#         self.edges.append(edge)
#         if target not in self.nodes:
#             self.nodes.append(target)

#     def execute(self, inputs: Dict[Node, Any]) -> Dict[Node, Any]:
#         """
#         Execute the graph and return the outputs of all nodes.
#         """
#         outputs = {}
#         for node in self.topological_sort():
#             if node in inputs:
#                 outputs[node] = node(inputs[node])
#             else:
#                 input_values = [outputs[edge.source] for edge in node.incoming_edges]
#                 outputs[node] = node(*input_values)
#         return outputs

#     def topological_sort(self) -> List[Node]:
#         """
#         Perform a topological sort of the nodes in the graph.
#         """
#         visited = set()
#         stack = []
#         for node in self.nodes:
#             if node not in visited:
#                 self._topological_sort_util(node, visited, stack)
#         return stack[::-1]  # return in reverse order

#     def _topological_sort_util(self, node: Node, visited: set, stack: List[Node]):
#         """
#         Helper function for topological sort.
#         """
#         visited.add(node)
#         for edge in node.outgoing_edges:
#             if edge.target not in visited:
#                 self._topological_sort_util(edge.target, visited, stack)
#         stack.append(node)

#     def validate(self) -> bool:
#         """
#         Validate the graph to ensure it is a Directed Acyclic Graph (DAG).
#         """
#         visited = set()
#         rec_stack = set()

#         for node in self.nodes:
#             if node not in visited:
#                 if self._has_cycle(node, visited, rec_stack):
#                     return False
#         return True

#     def _has_cycle(self, node: Node, visited: set, rec_stack: set) -> bool:
#         """
#         Helper function to check for cycles in the graph.
#         """
#         visited.add(node)
#         rec_stack.add(node)

#         for edge in node.outgoing_edges:
#             if edge.target not in visited:
#                 if self._has_cycle(edge.target, visited, rec_stack):
#                     return True
#             elif edge.target in rec_stack:
#                 return True

#         rec_stack.remove(node)
#         return False

#     def save(self, filename: str):
#         """
#         Save the graph to a file.
#         """
#         data = {
#             "nodes": [node.to_dict() for node in self.nodes],
#             "edges": [edge.to_dict() for edge in self.edges],
#         }
#         with open(filename, "w") as f:
#             yaml.dump(data, f)

#     @staticmethod
#     def load(filename: str) -> "Graph":
#         """
#         Load a graph from a file.
#         """
#         with open(filename, "r") as f:
#             data = yaml.load(f, Loader=yaml.FullLoader)
#         graph = Graph()
#         graph.nodes = [Node.from_dict(d) for d in data["nodes"]]
#         graph.edges = [Edge.from_dict(d, graph.nodes) for d in data["edges"]]
#         return graph
