from typing import Any, Optional
import logging
import tempfile

from geniusrise.core.data import OutputConfig, BatchOutputConfig, StreamingOutputConfig
from geniusrise.core.state import (
    StateManager,
    InMemoryStateManager,
    RedisStateManager,
    PostgresStateManager,
    DynamoDBStateManager,
)
from .task import Task, ECSManager, K8sManager


class Spout(Task):
    """
    Base class for all spouts.
    """

    def __init__(self, output_config: OutputConfig, state_manager: StateManager) -> None:
        """
        Initialize the spout.

        Args:
            output_config (OutputConfig): The output configuration.
            state_manager (StateManager): The state manager.
        """
        super().__init__()
        self.output_config = output_config
        self.state_manager = state_manager

        self.log = logging.getLogger(self.__class__.__name__)

    def __call__(self, method_name: str, *args, **kwargs) -> Any:
        """
        Execute a method locally and manage the state.

        Args:
            method_name (str): The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        try:
            # Get the type of state manager
            state_type = self.state_manager.get_state(self.id)

            # Save the current set of class variables to the state manager
            self.state_manager.set_state(self.id, dict(vars(self)))

            # Execute the task's method
            result = self.execute(method_name, *args, **kwargs)

            # Flush the output config
            self.output_config.flush()

            # Store the state as successful in the state manager
            state = dict(vars(self))
            state[f"{self.id}_success"] = True
            self.state_manager.set_state(self.id, state)

            return result
        except Exception as e:
            self.log.error(f"Failed to execute method '{method_name}': {e}")
            state = dict(vars(self))
            state[f"{self.id}_success"] = True
            self.state_manager.set_state(self.id, state)
            raise

    def execute_remote(self, manager_type: str, method_name: str, **kwargs) -> Optional[Any]:
        """
        Execute a method remotely and manage the state.

        Args:
            manager_type (str): The type of manager to use for remote execution ("ecs" or "k8s").
            method_name (str): The name of the method to execute.
            *args: Positional arguments to pass to the method.
            **kwargs: Keyword arguments to pass to the method.

        Returns:
            Any: The result of the method.
        """
        try:
            manager: StateManager | ECSManager | K8sManager
            if manager_type == "ecs":
                manager = ECSManager(
                    name=self.id,
                    image="geniusrise/geniusrise",
                    account_id=kwargs["account_id"] if "account_id" in kwargs else None,
                    security_group_ids=kwargs["security_group_ids"] if "security_group_ids" in kwargs else [],
                    command=["run", method_name] + [f"--{k} {v}" for k, v in kwargs.items()],
                    cluster=kwargs["cluster"] if "cluster" in kwargs else None,
                    subnet_ids=kwargs["subnet_ids"] if "subnet_ids" in kwargs else None,
                    replicas=kwargs["replicas"] if "replicas" in kwargs else None,
                    port=kwargs["port"] if "port" in kwargs else None,
                    log_group=kwargs["log_group"] if "log_group" in kwargs else None,
                    cpu=kwargs["cpu"] if "cpu" in kwargs else None,
                    memory=kwargs["memory"] if "memory" in kwargs else None,
                )

                # Create the task definition and run the task
                task_definition_arn = manager.create_task_definition()
                if task_definition_arn:
                    manager.run_task(task_definition_arn)
                else:
                    raise Exception(f"Could not create task definition {kwargs}")

                # Get the status of the task
                status = manager.describe_task(task_definition_arn)

            elif manager_type == "k8s":
                manager = K8sManager(
                    name=self.id,
                    namespace=kwargs["namespace"] if "namespace" in kwargs else "default",
                    image="geniusrise/geniusrise",
                    command=["run", method_name] + [f"--{k} {v}" for k, v in kwargs.items()],
                )

                # Run the task
                manager.run()

                # Get the status of the task
                status = manager.get_status()
            else:
                raise ValueError(f"Invalid manager type '{manager_type}'")

            # Store the status in the state manager
            if status:
                status["status"] = dict(status)
                self.state_manager.set_state(self.id, status)

                return status
            else:
                raise Exception(f"Could not save the status of this task {status.__dict__}")
        except Exception as e:
            status = dict(vars(self))
            status["status"] = False
            self.state_manager.set_state(self.id, status)
            self.log.exception(f"Failed to execute remote method '{method_name}': {e}")
            raise

    @staticmethod
    def create(output_type: str, state_type: str, task_type: str, **kwargs) -> "Spout":
        """
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            task_type (str): The type of task ("ecs" or "k8s").
            **kwargs: Additional keyword arguments for initializing the spout.

        Returns:
            Spout: The created spout.
        """
        # Create the output config
        output_config: BatchOutputConfig | StreamingOutputConfig
        if output_type == "batch":
            output_config = BatchOutputConfig(
                output_folder=kwargs["output_folder"] if "output_folder" in kwargs else tempfile.mkdtemp(),
                bucket=kwargs["bucket"] if "bucket" in kwargs else tempfile.mkdtemp(),
                s3_folder=kwargs["s3_folder"] if "s3_folder" in kwargs else tempfile.mkdtemp(),
            )
        elif output_type == "streaming":
            output_config = StreamingOutputConfig(
                kwargs["output_topic"] if "output_topic" in kwargs else None,
                kwargs["kafka_servers"] if "kafka_servers" in kwargs else None,
            )
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

        # Create the spout
        spout: Spout
        if task_type == "ecs":
            spout = Spout(output_config, state_manager, **kwargs)
        elif task_type == "k8s":
            spout = Spout(output_config, state_manager, **kwargs)
        else:
            raise ValueError(f"Invalid task type: {task_type}")

        return spout
