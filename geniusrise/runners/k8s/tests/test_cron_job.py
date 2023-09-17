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
import json
from geniusrise.runners.k8s.cron_job import CronJob
from geniusrise.runners.k8s.base import K8sResourceManager
from argparse import Namespace
import subprocess
import time


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
