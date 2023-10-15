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

import subprocess
import time

import pytest

from geniusrise.runners.k8s.base import K8sResourceManager


@pytest.fixture(scope="module")
def k8s_manager():
    subprocess.run(["kubectl", "run", "test-pod", "--image=nginx", "--namespace=geniusrise"])

    manager = K8sResourceManager()
    args = {
        "kube_config_path": "~/.kube/config",
        "cluster_name": "geniusrise-dev",
        "context_name": "arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev",
        "namespace": "geniusrise",
        "labels": None,
        "annotations": None,
        "api_key": None,
        "api_host": None,
        "verify_ssl": True,
        "ssl_ca_cert": None,
    }
    manager.connect(**args)

    # Wait for the pod to be running
    for _ in range(60):  # Wait up to 60 seconds
        status = manager.status("test-pod")
        if status == "Running":
            break
        time.sleep(1)
    else:
        pytest.fail("Pod did not start in time")

    yield manager, args

    subprocess.run(["kubectl", "delete", "pod", "test-pod", "--namespace=geniusrise"])


def test_status(k8s_manager):
    manager, args = k8s_manager
    manager.connect(**args)

    status = manager.status("test-pod")
    assert status == "Running"


def test_show(k8s_manager):
    manager, args = k8s_manager
    manager.connect(**args)

    pods = manager.show()
    assert len(pods) >= 1
    assert "test" in pods[0]["name"]


def test_describe(k8s_manager):
    manager, args = k8s_manager
    manager.connect(**args)

    description = manager.describe("test-pod")
    assert description["name"] == "test-pod"
    assert description["status"] == "Running"
    assert description["containers"][0] == "test-pod"


def test_logs(k8s_manager):
    manager, args = k8s_manager
    manager.connect(**args)

    logs = manager.logs("test-pod", tail=10, follow=False)
    assert logs is not None
