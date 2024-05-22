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
from geniusrise.runners.openstack.autoscale import OpenStackAutoscaleRunner
from test_config import (
    AUTH_URL,
    USERNAME,
    PASSWORD,
    PROJECT_NAME,
    TEST_AUTOSCALE_NAME,
    TEST_IMAGE,
    TEST_FLAVOR,
    TEST_KEY_NAME,
    TEST_NETWORK,
    TEST_SUBNET,
    TEST_MIN_INSTANCES,
    TEST_MAX_INSTANCES,
    TEST_DESIRED_INSTANCES,
    TEST_PROTOCOL,
    TEST_SCALE_UP_THRESHOLD,
    TEST_SCALE_UP_ADJUSTMENT,
    TEST_SCALE_DOWN_THRESHOLD,
    TEST_SCALE_DOWN_ADJUSTMENT,
    TEST_ALARM_PERIOD,
    TEST_ALARM_EVALUATION_PERIODS,
    TEST_USER_DATA,
    TEST_BLOCK_STORAGE_SIZE,
    TEST_OPEN_PORTS,
)


@pytest.fixture(scope="module")
def openstack_autoscale_manager():
    manager = OpenStackAutoscaleRunner()
    manager.connect(
        auth_url=AUTH_URL,
        username=USERNAME,
        password=PASSWORD,
        project_name=PROJECT_NAME,
    )
    yield manager
    manager.delete(name=TEST_AUTOSCALE_NAME)


def test_create_autoscale(openstack_autoscale_manager):
    autoscale = openstack_autoscale_manager.create(
        name=TEST_AUTOSCALE_NAME,
        image=TEST_IMAGE,
        flavor=TEST_FLAVOR,
        key_name=TEST_KEY_NAME,
        network=TEST_NETWORK,
        subnet=TEST_SUBNET,
        min_instances=TEST_MIN_INSTANCES,
        max_instances=TEST_MAX_INSTANCES,
        desired_instances=TEST_DESIRED_INSTANCES,
        protocol=TEST_PROTOCOL,
        scale_up_threshold=TEST_SCALE_UP_THRESHOLD,
        scale_up_adjustment=TEST_SCALE_UP_ADJUSTMENT,
        scale_down_threshold=TEST_SCALE_DOWN_THRESHOLD,
        scale_down_adjustment=TEST_SCALE_DOWN_ADJUSTMENT,
        alarm_period=TEST_ALARM_PERIOD,
        alarm_evaluation_periods=TEST_ALARM_EVALUATION_PERIODS,
        user_data=TEST_USER_DATA,
        block_storage_size=TEST_BLOCK_STORAGE_SIZE,
        open_ports=TEST_OPEN_PORTS,
    )

    assert autoscale.name == f"{TEST_AUTOSCALE_NAME}-stack"
    assert autoscale.status == "CREATE_COMPLETE"


# def test_status_autoscale(openstack_autoscale_manager):
#     autoscale = openstack_autoscale_manager.status(name=TEST_AUTOSCALE_NAME)

#     assert autoscale.name == f"{TEST_AUTOSCALE_NAME}-stack"
#     assert autoscale.status == "CREATE_COMPLETE"


# def test_delete_autoscale(openstack_autoscale_manager):
#     openstack_autoscale_manager.delete(name=TEST_AUTOSCALE_NAME)

#     time.sleep(5)
#     with pytest.raises(Exception):
#         openstack_autoscale_manager.conn.orchestration.find_stack(f"{TEST_AUTOSCALE_NAME}-stack")
