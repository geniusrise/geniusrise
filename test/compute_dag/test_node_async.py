import pytest
import asyncio
from typing import Any

from geniusrise_cli.compute_dag.dsl import parse_pipeline


# Define some async functions for testing
async def start(_=None) -> int:
    await asyncio.sleep(0.1)  # simulate IO delay
    return 2


async def node1(x: int) -> int:
    await asyncio.sleep(0.1)  # simulate IO delay
    return x + 1


async def restructure1(x: int) -> int:
    await asyncio.sleep(0.1)  # simulate IO delay
    return x * 2


async def node2(x: Any) -> int:
    await asyncio.sleep(0.1)  # simulate IO delay
    y = await x  # await the result of x
    if y < 0:
        raise ValueError("Input must be non-negative")
    return y**2


async def node3(x: int) -> int:
    await asyncio.sleep(0.1)  # simulate IO delay
    return x + 1


# Test the string-based DSL
@pytest.mark.asyncio
async def test_node_async():
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
    assert reduced_value == 37  # The pipeline only has one output, so the reduced value is the same as the output
