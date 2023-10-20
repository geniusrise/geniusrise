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

import json
import subprocess
import time
from argparse import Namespace

import pytest

from geniusrise.runners.k8s.base import K8sResourceManager
from geniusrise.runners.k8s.service import Service


@pytest.fixture(scope="module")
def k8s_manager():
    subprocess.run(["kubectl", "run", "test-pod", "--image=nginx", "--namespace=geniusrise"])

    manager = K8sResourceManager()
    args = {
        "kube_config_path": "~/.kube/config",
        "cluster_name": "geniusrise-dev",
        "context_name": "arn:aws:eks:us-east-1:143601010266:cluster/geniusrise-dev",
        "namespace": "geniusrise",
        "labels": {"created_by": "geniusrise"},
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


@pytest.fixture(scope="module")
def service_manager(k8s_manager):
    m, a = k8s_manager

    manager = Service()
    args = Namespace(**a)
    manager.connect(
        kube_config_path=args.kube_config_path,
        cluster_name=args.cluster_name,
        context_name=args.context_name,
        namespace=args.namespace,
        labels=args.labels,
        annotations=args.annotations,
        api_key=args.api_key,
        api_host=args.api_host,
        verify_ssl=args.verify_ssl,
        ssl_ca_cert=args.ssl_ca_cert,
    )
    yield manager


def test_create_service(service_manager):
    args = Namespace(
        name="test-service",
        image="nginx",
        command=["nginx", "-g", "daemon off;"],
        replicas=1,
        port=80,
        target_port=8080,
        env_vars=json.dumps({"TEST_ENV": "test_value"}),
    )
    service_manager.create(
        args.name,
        args.image,
        args.command,
        replicas=args.replicas,
        port=args.port,
        target_port=args.target_port,
        env_vars=json.loads(args.env_vars),
    )
    services = service_manager.show()
    print(services)
    assert any(service["name"] == f"{args.name}" for service in services)


def test_describe_service(service_manager):
    args = Namespace(name="test-service")
    service = service_manager.describe(f"{args.name}")
    assert service["name"] == f"{args.name}"


def test_status_service(service_manager):
    args = Namespace(name="test-service")
    status = service_manager.status(args.name)
    assert "deployment_status" in status


def test_delete_service(service_manager):
    args = Namespace(name="test-service")
    service_manager.delete(args.name)
    services = service_manager.show()
    assert all(service["name"] != f"{args.name}-service" for service in services)
