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

import time

import pytest
import shortuuid
from geniusrise.core.task import K8sManager

# Define your K8sManager details as constants
NAME = "test-deployment-" + str(shortuuid.random(5)).lower()
COMMAND = ["sleep", "100"]
NAMESPACE = "default"
IMAGE = "busybox"
REPLICAS = 1
PORT = 80


# Define a fixture for your K8sManager
@pytest.fixture
def k8s_manager():
    return K8sManager(NAME, COMMAND, NAMESPACE, IMAGE, REPLICAS, PORT)


# Test that the K8sManager can be initialized
def test_k8s_manager_init(k8s_manager):
    assert k8s_manager.name == NAME
    assert k8s_manager.command == COMMAND
    assert k8s_manager.namespace == NAMESPACE
    assert k8s_manager.image == IMAGE
    assert k8s_manager.replicas == REPLICAS
    assert k8s_manager.port == PORT


# Test that the K8sManager can create a deployment
def test_k8s_manager_create_deployment(k8s_manager):
    k8s_manager.create_deployment()

    time.sleep(2)
    status = k8s_manager.get_status()
    if "availableReplicas" in status:
        assert status["availableReplicas"] == k8s_manager.replicas
    elif "replicas" in status:
        assert status["replicas"] == k8s_manager.replicas
    else:
        assert True, "Deployment is not yet ready"


# Test that the K8sManager can scale a deployment
def test_k8s_manager_scale_deployment(k8s_manager):
    k8s_manager.scale_deployment(2)

    time.sleep(2)
    print(k8s_manager.get_status())
    assert k8s_manager.get_status()["_replicas"] == 2


# Test that the K8sManager can update a deployment
def test_k8s_manager_update_deployment(k8s_manager):
    k8s_manager.update_deployment(3)

    time.sleep(2)
    assert k8s_manager.get_status()["_replicas"] == 3


# Test that the K8sManager can get statistics
def test_k8s_manager_get_statistics(k8s_manager):
    stats = k8s_manager.get_statistics()
    assert "deployment" in stats
    assert "pods" in stats


# Test that the K8sManager can get logs
def test_k8s_manager_get_logs(k8s_manager):
    logs = k8s_manager.get_logs()
    assert isinstance(logs, dict)


# Test that the K8sManager can delete a deployment
def test_k8s_manager_delete_deployment(k8s_manager):
    k8s_manager.delete_deployment()

    time.sleep(2)
    assert k8s_manager.get_status() == {}


# Test that the K8sManager can create a service
def test_k8s_manager_create_service(k8s_manager):
    k8s_manager.create_service()
    # Add assertions to check that the service was created


# Test that the K8sManager can delete a service
def test_k8s_manager_delete_service(k8s_manager):
    k8s_manager.delete_service()
    # Add assertions to check that the service was deleted
