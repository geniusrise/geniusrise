# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import pytest

from geniusrise.core.task import ECSManager

# Hardcode your AWS resources here
ACCPUNT_ID = "866011655254"
CLUSTER = "test-cluster"
SUBNET_IDS = ["subnet-28ce4853", "subnet-99700cd5"]
SECURITY_GROUP_IDS = ["sg-0e236b30891c3ed6d"]
TASK_NAME = "test-task"
TASK_COMMAND = ["echo", "hello"]
TASK_IMAGE = "alpine"
TASK_PORT = 8080


@pytest.fixture(scope="module")
def ecs_manager():
    return ECSManager(
        name=TASK_NAME,
        command=TASK_COMMAND,
        cluster=CLUSTER,
        subnet_ids=SUBNET_IDS,
        security_group_ids=SECURITY_GROUP_IDS,
        image=TASK_IMAGE,
        port=TASK_PORT,
        account_id=ACCPUNT_ID,
    )


def test_create_task_definition(ecs_manager):
    task_definition_arn = ecs_manager.create_task_definition()
    assert "arn:aws:ecs:ap-south-1:866011655254:task-definition/test-task:" in task_definition_arn


def test_run_task(ecs_manager):
    task_definition_arn = ecs_manager.create_task_definition()
    response = ecs_manager.run_task(task_definition_arn)
    assert response["failures"] == []
    assert response["tasks"][0]["cpu"] == "256"
    assert response["tasks"][0]["launchType"] == "FARGATE"


def test_describe_task(ecs_manager):
    task_definition_arn = ecs_manager.create_task_definition()
    task = ecs_manager.run_task(task_definition_arn)
    response = ecs_manager.describe_task(task["tasks"][0]["taskArn"])
    assert response is not None


def test_stop_task(ecs_manager):
    task_definition_arn = ecs_manager.create_task_definition()
    task = ecs_manager.run_task(task_definition_arn)
    response = ecs_manager.stop_task(task["tasks"][0]["taskArn"])
    assert response is not None


# def test_create_service(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     response = ecs_manager.create_service(task_definition_arn)
#     assert response is not None


# def test_update_service(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     ecs_manager.create_service(task_definition_arn)
#     new_task_definition_arn = ecs_manager.create_task_definition()
#     response = ecs_manager.update_service(new_task_definition_arn)
#     assert response is not None


# def test_delete_service(ecs_manager):
#     task_definition_arn = ecs_manager.create_task_definition()
#     ecs_manager.create_service(task_definition_arn)
#     response = ecs_manager.delete_service()
#     assert response is not None
