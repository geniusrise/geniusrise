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
from geniusrise.runners.k8s.cron_job import CronJob


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
def cronjob_manager(k8s_manager):
    m, a = k8s_manager

    manager = CronJob()
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


def test_create(cronjob_manager):
    args = Namespace(
        name="test-cronjob",
        image="busybox",
        command=["/bin/sh", "-c", "date"],
        schedule="*/1 * * * *",
        env_vars=json.dumps({"TEST_ENV": "test_value"}),
    )
    cronjob_manager.create(
        name=args.name,
        image=args.image,
        command=args.command,
        schedule=args.schedule,
        env_vars=json.loads(args.env_vars),
    )
    cronjob_status = cronjob_manager.status(args.name)
    assert cronjob_status["cronjob_status"] is not None


def test_status(cronjob_manager):
    args = Namespace(name="test-cronjob")
    cronjob_status = cronjob_manager.status(args.name)
    assert cronjob_status["cronjob_status"] is not None


def test_delete(cronjob_manager):
    args = Namespace(name="test-cronjob")
    cronjob_manager.delete(args.name)
    try:
        cronjob_manager.status(args.name)
    except Exception as e:
        assert "not found" in str(e)
