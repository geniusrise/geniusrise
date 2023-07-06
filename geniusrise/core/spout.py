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
        The `Spout` class is a base class for all spouts in the given context.
        It inherits from the `Task` class and provides methods for executing tasks
        both locally and remotely, as well as managing their state, with state management
        options including in-memory, Redis, PostgreSQL, and DynamoDB,
        and output configurations for batch or streaming data.

        The `Spout` class uses the `OutputConfig` and `StateManager` classes, which are abstract base
         classes for managing output configurations and states, respectively. The `OutputConfig` class
         has two subclasses: `StreamingOutputConfig` and `BatchOutputConfig`, which manage streaming and
         batch output configurations, respectively. The `StateManager` class is used to get and set state,
         and it has several subclasses for different types of state managers.

        The `Spout` class also uses the `ECSManager` and `K8sManager` classes in the `execute_remote` method,
        which are used to manage tasks on Amazon ECS and Kubernetes, respectively.

        Usage:
            - Create an instance of the Spout class by providing an OutputConfig object and a StateManager object.
            - The OutputConfig object specifies the output configuration for the spout.
            - The StateManager object handles the management of the spout's state.

        Example:
            output_config = OutputConfig(...)
            state_manager = StateManager(...)
            spout = Spout(output_config, state_manager)

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
                Keyword Arguments:
                    - Additional keyword arguments specific to the method.

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
            **kwargs: Keyword arguments to pass to the method.
                Keyword Arguments:
                    - name (str): The name argument.
                    - account_id (str): The account ID argument.
                    - cluster (str): The cluster argument.
                    - subnet_ids (str): The subnet IDs argument.
                    - security_group_ids (str): The security group IDs argument.
                    - image (str): The image argument.
                    - replicas (str): The replicas argument.
                    - port (str): The port argument.
                    - log_group (str): The log group argument.
                    - cpu (str): The CPU argument.
                    - memory (str): The memory argument.

        Returns:
            Any: The result of the method.
        """
        try:
            manager: StateManager | ECSManager | K8sManager
            if manager_type == "ecs":
                manager = ECSManager(
                    name=kwargs["name"] if "name" in kwargs else None,
                    account_id=kwargs["account_id"] if "account_id" in kwargs else None,
                    cluster=kwargs["cluster"] if "cluster" in kwargs else None,
                    subnet_ids=kwargs["subnet_ids"] if "subnet_ids" in kwargs else None,
                    security_group_ids=kwargs["security_group_ids"] if "security_group_ids" in kwargs else None,
                    image=kwargs["image"] if "image" in kwargs else None,
                    replicas=kwargs["replicas"] if "replicas" in kwargs else None,
                    port=kwargs["port"] if "port" in kwargs else None,
                    log_group=kwargs["log_group"] if "log_group" in kwargs else None,
                    cpu=kwargs["cpu"] if "cpu" in kwargs else None,
                    memory=kwargs["memory"] if "memory" in kwargs else None,
                    command=["run", method_name] + [f"--{k} {v}" for k, v in kwargs.items()],
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
                    name=kwargs["name"] if "name" in kwargs else None,
                    namespace=kwargs["namespace"] if "namespace" in kwargs else None,
                    image=kwargs["image"] if "image" in kwargs else None,
                    replicas=kwargs["replicas"] if "replicas" in kwargs else None,
                    port=kwargs["port"] if "port" in kwargs else None,
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
    def create(output_type: str, state_type: str, **kwargs) -> "Spout":
        """
        Create a spout of a specific type.

        Args:
            output_type (str): The type of output config ("batch" or "streaming").
            state_type (str): The type of state manager ("in_memory", "redis", "postgres", or "dynamodb").
            **kwargs: Additional keyword arguments for initializing the spout.
                Keyword Arguments:
                    - output_folder (str): The output folder argument.
                    - bucket (str): The bucket argument.
                    - s3_folder (str): The S3 folder argument.
                    - redis_host (str): The Redis host argument.
                    - redis_port (str): The Redis port argument.
                    - redis_db (str): The Redis database argument.
                    - postgres_host (str): The PostgreSQL host argument.
                    - postgres_port (str): The PostgreSQL port argument.
                    - postgres_user (str): The PostgreSQL user argument.
                    - postgres_password (str): The PostgreSQL password argument.
                    - postgres_database (str): The PostgreSQL database argument.
                    - postgres_table (str): The PostgreSQL table argument.
                    - dynamodb_table_name (str): The DynamoDB table name argument.
                    - dynamodb_region_name (str): The DynamoDB region name argument.

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
            state_manager = RedisStateManager(
                host=kwargs["redis_host"] if "redis_host" in kwargs else None,
                port=kwargs["redis_port"] if "redis_port" in kwargs else None,
                db=kwargs["redis_db"] if "redis_db" in kwargs else None,
            )
        elif state_type == "postgres":
            state_manager = PostgresStateManager(
                host=kwargs["postgres_host"] if "postgres_host" in kwargs else None,
                port=kwargs["postgres_port"] if "postgres_port" in kwargs else None,
                user=kwargs["postgres_user"] if "postgres_user" in kwargs else None,
                password=kwargs["postgres_password"] if "postgres_password" in kwargs else None,
                database=kwargs["postgres_database"] if "postgres_database" in kwargs else None,
                table=kwargs["postgres_table"] if "postgres_table" in kwargs else None,
            )
        elif state_type == "dynamodb":
            state_manager = DynamoDBStateManager(
                table_name=kwargs["dynamodb_table_name"] if "table_name" in kwargs else None,
                region_name=kwargs["dynamodb_region_name"] if "region_name" in kwargs else None,
            )
        else:
            raise ValueError(f"Invalid state type: {state_type}")

        # Create the spout
        spout = Spout(output_config, state_manager)
        return spout
