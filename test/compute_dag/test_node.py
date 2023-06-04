import pytest

from geniusrise_cli.compute_dag.dsl import parse_pipeline


# Define some functions for testing
def start(_=None) -> int:
    return 2


def node1(x: int) -> int:
    return x + 1


def restructure1(x: int) -> int:
    return x * 2


def node2(x: int) -> int:
    if x < 0:
        raise ValueError("Input must be non-negative")
    return x**2


def node3(x: int) -> int:
    return x + 1


# Test the string-based DSL
@pytest.mark.asyncio
@pytest.mark.asyncio
async def test_nodes():
    # Define a pipeline in the DSL
    pipeline_str = "start -[noop]-> node1 -[restructure1]-> node2 -[noop]-> node3"

    # Parse the pipeline
    pipeline = parse_pipeline(pipeline_str, globals())

    # Test the __call__ method
    assert (await pipeline()).value == 37

    # Test the map method
    mapped_pipeline = await pipeline.map(lambda x: x + 1)
    assert (await mapped_pipeline(0)).value == 65

    # Test the reduce method
    reduced_value = await pipeline.reduce(lambda x, y: x + y, 0)
    assert reduced_value == 37
