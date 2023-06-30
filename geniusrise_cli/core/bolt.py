from .input_config import BatchInputConfig, StreamingInputConfig
from .output_config import BatchOutputConfig, StreamingOutputConfig
from .state_manager import (
    StateManager,
    InMemoryStateManager,
    RedisStateManager,
    PostgresStateManager,
    DynamoDBStateManager,
)
from .task import Task, ECSTask, K8sTask


class BoltFactory:
    """
    Factory class for creating bolts of various types.
    """

    @staticmethod
    def create_bolt(input_type: str, output_type: str, state_type: str, task_type: str, **kwargs):
        """
        Create a bolt of a specific type.

        Args:
            input_type (str): The type of input config ("batch" or "streaming").
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            task_type (str): The type of task ("ecs" or "k8s").
            **kwargs: Additional keyword arguments for initializing the bolt.

        Returns:
            Task: The created bolt.
        """
        # Create the input config
        if input_type == "batch":
            input_config = BatchInputConfig(**kwargs)
        elif input_type == "streaming":
            input_config = StreamingInputConfig(**kwargs)
        else:
            raise ValueError(f"Invalid input type: {input_type}")

        # Create the output config
        if output_type == "batch":
            output_config = BatchOutputConfig(**kwargs)
        elif output_type == "streaming":
            output_config = StreamingOutputConfig(**kwargs)
        else:
            raise ValueError(f"Invalid output type: {output_type}")

        # Create the state manager
        state_manager: StateManager
        if state_type == "in_memory":
            state_manager = InMemoryStateManager()
        elif state_type == "redis":
            state_manager = RedisStateManager(**kwargs)
        elif state_type == "postgres":
            state_manager = PostgresStateManager(**kwargs)
        elif state_type == "dynamodb":
            state_manager = DynamoDBStateManager(**kwargs)
        else:
            raise ValueError(f"Invalid state type: {state_type}")

        # Create the task
        task: Task
        if task_type == "ecs":
            task = ECSTask(input_config, output_config, state_manager, **kwargs)
        elif task_type == "k8s":
            task = K8sTask(input_config, output_config, state_manager, **kwargs)
        else:
            raise ValueError(f"Invalid task type: {task_type}")

        return task
