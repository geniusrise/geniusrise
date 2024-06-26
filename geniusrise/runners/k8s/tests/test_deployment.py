# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import subprocess
import time
from argparse import Namespace

import pytest

from geniusrise.runners.k8s.base import K8sResourceManager
from geniusrise.runners.k8s.deployment import Deployment


@pytest.fixture(scope="module")
def k8s_manager():
    subprocess.run(["kubectl", "run", "test-pod", "--image=nginx", "--namespace=geniusrise"])

    manager = K8sResourceManager()
    args = {
        "kube_config_path": "~/.kube/config",
        "cluster_name": "geniusrise-dev",
        "context_name": "arn:aws:eks:us-east-1:genius-dev:cluster/geniusrise-dev",
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
def deployment_manager(k8s_manager):
    m, a = k8s_manager

    manager = Deployment()
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
    # manager.delete("test-deployment")


def test_create_deployment(deployment_manager):
    args = Namespace(
        name="test-deployment",
        image="nginx",
        command=["nginx", "-g", "daemon off;"],
        replicas=1,
        env_vars=json.dumps({"TEST_ENV": "test_value"}),
    )
    deployment_manager.create(
        args.name,
        args.image,
        args.command,
        replicas=args.replicas,
        env_vars=json.loads(args.env_vars),
    )
    deployments = deployment_manager.show()
    assert any(deployment["name"] == args.name for deployment in deployments)


def test_scale_deployment(deployment_manager):
    args = Namespace(name="test-deployment", replicas=2)
    deployment_manager.scale(args.name, args.replicas)
    deployment = deployment_manager.describe(args.name)
    assert deployment["replicas"] == args.replicas


def test_describe_deployment(deployment_manager):
    args = Namespace(name="test-deployment")
    deployment = deployment_manager.describe(args.name)
    assert deployment["name"] == args.name


def test_status_deployment(deployment_manager):
    args = Namespace(name="test-deployment")
    status = deployment_manager.status(args.name)
    assert "deployment_status" in status


def test_delete_deployment(deployment_manager):
    args = Namespace(name="test-deployment")
    deployment_manager.delete(args.name)
    deployments = deployment_manager.show()
    assert all(deployment["name"] != args.name for deployment in deployments)
