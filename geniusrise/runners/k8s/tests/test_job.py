import pytest
import json
from geniusrise.runners.k8s.job import Job
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
def job_manager(k8s_manager):
    m, a = k8s_manager

    manager = Job()
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
    # manager.delete("test-job")


def test_create_job(job_manager):
    args = Namespace(
        name="test-job",
        image="busybox",
        command="echo 'Hello, World!'",
        env_vars=json.dumps({"TEST_ENV": "test_value"}),
    )
    job_manager.create(args.name, args.image, args.command.split(), env_vars=json.loads(args.env_vars))
    status = job_manager.status(args.name)
    assert "job_status" in status


def test_status_job(job_manager):
    args = Namespace(name="test-job")
    status = job_manager.status(args.name)
    assert "job_status" in status


def test_delete_job(job_manager):
    args = Namespace(name="test-job")
    job_manager.delete(args.name)
    try:
        job_manager.status(args.name)
    except Exception as e:
        assert "not found" in str(e)
