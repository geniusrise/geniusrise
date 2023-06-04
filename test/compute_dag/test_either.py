import pytest
from geniusrise_cli.compute_dag.types import Either


# Define some functions for testing
def func1(x: int) -> int:
    return x + 1


async def func11(x: int) -> int:
    return x + 1


# Test the Either class
@pytest.mark.asyncio
async def test_either():
    # Test the ok method
    e = Either.ok(42)
    assert not e.is_error()
    assert e.value == 42

    # Test the error method
    e = Either.error(ValueError("An error occurred"))
    assert e.is_error()
    assert isinstance(e.error, ValueError)

    # Test the map method
    e = await Either.ok(42).map(func1)
    assert e.value == 43  # 42 + 1 = 43

    e = await Either.ok(42).map(func11)
    assert e.value == 43  # 42 + 1 = 43

    # Test the reduce method
    result = await Either.ok(42).reduce(lambda x, y: x + y, 0)
    assert result == 42  # 0 + 42 = 42

    # Test the foldLeft and foldRight methods
    result = await Either.ok(42).foldLeft(lambda x, y: x + y, 0)
    assert result == 42  # 0 + 42 = 42
    result = await Either.ok(42).foldRight(lambda x, y: x + y, 0)
    assert result == 42  # 0 + 42 = 42
