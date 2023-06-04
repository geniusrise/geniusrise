import inspect
from typing import Callable, Any, Optional


class Either:
    """
    A simple Either type for error handling.
    """

    def __init__(self, value: Any, error: Optional[Exception] = None):
        self.error = error  # type: ignore
        self.value = value

    @classmethod
    def ok(cls, value: Any):
        """
        Creates an Either representing a successful computation.
        """
        return cls(value)

    @classmethod
    def error(cls, error: Exception):
        """
        Creates an Either representing a failed computation.
        """
        return cls(None, error)

    def is_error(self) -> bool:
        """
        Checks whether this Either represents an error.
        """
        return self.error is not None

    async def map(self, function: Callable[[Any], Any]) -> "Either":
        """
        Applies a function to the value if this is an 'ok' Either.
        """
        if self.is_error():
            return self
        else:
            if inspect.iscoroutinefunction(function):
                return Either.ok(await function(self.value))
            else:
                return Either.ok(function(self.value))

    async def reduce(self, function: Callable[[Any, Any], Any], initial_value: Any) -> Any:
        """
        Applies a function to the initial value and the value of this Either if this is an 'ok' Either.
        """
        if self.is_error():
            return initial_value
        else:
            if inspect.iscoroutinefunction(function):
                return await function(initial_value, self.value)
            else:
                return function(initial_value, self.value)

    async def foldLeft(self, function: Callable[[Any, Any], Any], initial_value: Any) -> Any:
        """
        Left fold. Equivalent to reduce for Either.
        """
        return await self.reduce(function, initial_value)

    async def foldRight(self, function: Callable[[Any, Any], Any], initial_value: Any) -> Any:
        """
        Right fold. Equivalent to reduce for Either.
        """
        return await self.reduce(function, initial_value)

    async def compose(self, other: "Either", function: Callable[[Any, Any], Any]) -> "Either":
        """
        Composes this Either with another Either using a binary function.
        """
        if self.is_error():
            return self
        elif other.is_error():
            return other
        else:
            if inspect.iscoroutinefunction(function):
                return Either.ok(await function(self.value, other.value))
            else:
                return Either.ok(function(self.value, other.value))
