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

import pytest
import time
from geniusrise.runners.openstack.instance import OpenStackInstanceRunner
from test_config import (
    AUTH_URL,
    USERNAME,
    PASSWORD,
    PROJECT_NAME,
    TEST_INSTANCE_NAME,
    TEST_IMAGE,
    TEST_FLAVOR,
    TEST_KEY_NAME,
    TEST_NETWORK,
    TEST_BLOCK_STORAGE_SIZE,
    TEST_OPEN_PORTS,
    TEST_USER_DATA,
)


@pytest.fixture(scope="module")
def openstack_manager():
    manager = OpenStackInstanceRunner()
    manager.connect(
        auth_url=AUTH_URL,
        username=USERNAME,
        password=PASSWORD,
        project_name=PROJECT_NAME,
    )
    yield manager


def test_create_instance(openstack_manager):
    instance = openstack_manager.create(
        name=TEST_INSTANCE_NAME,
        image=TEST_IMAGE,
        flavor=TEST_FLAVOR,
        key_name=TEST_KEY_NAME,
        allocate_ip=True,
        network=TEST_NETWORK,
        block_storage_size=TEST_BLOCK_STORAGE_SIZE,
        open_ports=TEST_OPEN_PORTS,
        user_data=TEST_USER_DATA,
    )

    assert instance.name == TEST_INSTANCE_NAME


def test_status_instance(openstack_manager):
    instance = openstack_manager.status(name=TEST_INSTANCE_NAME)

    assert instance is not None
    assert instance.name == TEST_INSTANCE_NAME
    assert instance.status in ["ACTIVE", "BUILD"]


def test_delete_instance(openstack_manager):
    openstack_manager.delete(name=TEST_INSTANCE_NAME)

    time.sleep(5)
    server = openstack_manager.conn.compute.find_server(TEST_INSTANCE_NAME)
    assert server is None
