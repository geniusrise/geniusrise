import pytest
from geniusrise.core.task import ECSManager

# Define your ECSManager details as constants
CLUSTER = "test-cluster"
NAME = "test-task"
COMMAND = ["echo", "hello"]
IMAGE = "busybox"
REPLICAS = 1
PORT = 80
LOG_GROUP = "/ecs/geniusrise-test-task"
SUBNET_IDS = ["subnet-28ce4853", "subnet-99700cd5"]


# Define a fixture for your ECSManager
@pytest.fixture
def ecs_manager():
    return ECSManager(
        name=NAME,
        command=COMMAND,
        image=IMAGE,
        replicas=REPLICAS,
        port=PORT,
        log_group=LOG_GROUP,
        cluster=CLUSTER,
        subnet_ids=SUBNET_IDS,
    )


# Test that the ECSManager can be initialized
def test_ecs_manager_init(ecs_manager):
    assert ecs_manager.name == NAME
    assert ecs_manager.command == COMMAND
    assert ecs_manager.image == IMAGE
    assert ecs_manager.replicas == REPLICAS
    assert ecs_manager.port == PORT
    assert ecs_manager.log_group == LOG_GROUP


# Test that the ECSManager can create a task definition
def test_ecs_manager_create_task_definition(ecs_manager):
    task_definition_arn = ecs_manager.create_task_definition()
    assert task_definition_arn is not None


# # Test that the ECSManager can run a task
# def test_ecs_manager_run_task(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     response = ecs_manager.run_task(task_definition_arn)
#     assert response is not None


# # Test that the ECSManager can describe a task
# def test_ecs_manager_describe_task(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     ecs_manager.run_task(task_definition_arn)
#     response = ecs_manager.describe_task(task_definition_arn)
#     assert response is not None


# # Test that the ECSManager can stop a task
# def test_ecs_manager_stop_task(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     ecs_manager.run_task(task_definition_arn)
#     response = ecs_manager.stop_task(task_definition_arn)
#     assert response is not None


# # Test that the ECSManager can update a task
# def test_ecs_manager_update_task(ecs_manager):
#     new_image = "alpine"
#     new_command = ["echo", "world"]
#     ecs_manager.update_task(new_image, new_command)
#     assert ecs_manager.image == new_image
#     assert ecs_manager.command == new_command
