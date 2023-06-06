import pytest
from geniusrise_cli.compute_dag.dsl import parse_pipeline


# Define some functions for testing
def start() -> int:
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


def node4(x: int) -> int:
    return x - 1


def node5(x: int) -> int:
    return x // 2


# Test the string-based DSL
@pytest.mark.asyncio
async def test_dsl_complex_1():
    pipeline_str = "start -[noop]-> node1 -[restructure1]-> node2 -[noop]-> node3 -[noop]-> node4"
    pipeline = parse_pipeline(pipeline_str, globals())
    assert (await pipeline()).value == 36


@pytest.mark.asyncio
async def test_dsl_complex_2():
    pipeline_str = "start -[noop]-> node1 -[restructure1]-> node2 -[noop]-> node3 -[noop]-> node5"
    pipeline = parse_pipeline(pipeline_str, globals())
    assert (await pipeline()).value == 18


@pytest.mark.asyncio
async def test_dsl_complex_3():
    pipeline_str = "start -[noop]-> node1 -[restructure1]-> node2 -[noop]-> node4 -[noop]-> node5"
    pipeline = parse_pipeline(pipeline_str, globals())
    assert (await pipeline()).value == 17


@pytest.mark.asyncio
async def test_dsl_complex_4():
    pipeline_str = "start -[noop]-> node1 -[restructure1]-> node4 -[noop]-> node5 -[noop]-> node3"
    pipeline = parse_pipeline(pipeline_str, globals())
    assert (await pipeline()).value == 3


@pytest.mark.asyncio
async def test_dsl_complex_5():
    pipeline_str = "start -[noop]-> node4 -[restructure1]-> node5 -[noop]-> node3 -[noop]-> node1"
    pipeline = parse_pipeline(pipeline_str, globals())
    assert (await pipeline()).value == 3
