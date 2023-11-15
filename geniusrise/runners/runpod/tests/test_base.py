import pytest
from geniusrise.runners.runpod.base import RunPodResourceManager


# Fixture for the resource manager instance
@pytest.fixture
def resource_manager():
    return RunPodResourceManager()


# Test for __init__ method
def test_init(resource_manager):
    assert resource_manager.api_key is not None, "API key should be loaded from environment"


def test_create_pod(resource_manager):
    pod = resource_manager.create_pod(
        pod_name="geniusrise-test-pod",
        image_name="geniusrise/geniusrise",
        gpu_type_id="NVIDIA GeForce RTX 4090",
        support_public_ip=True,
        start_ssh=True,
        gpu_count=1,
        volume_in_gb=100,
        container_disk_in_gb=100,
        min_vcpu_count=4,
        min_memory_in_gb=100,
        docker_args="genius list",
        ports="1337",
        volume_mount_path="/data",
        env={},
    )

    print(pod)
    assert 1 == 2
