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

import os

AUTH_URL = os.environ["OPENSTACK_AUTH_URL"]
USERNAME = os.environ["OPENSTACK_USERNAME"]
PASSWORD = os.environ["OPENSTACK_PASSWORD"]
PROJECT_NAME = os.environ["OPENSTACK_PROJECT_NAME"]

TEST_INSTANCE_NAME = os.environ["OPENSTACK_INSTANCE_NAME"]
TEST_IMAGE = os.environ["OPENSTACK_IMAGE"]
TEST_FLAVOR = os.environ["OPENSTACK_FLAVOR"]
TEST_KEY_NAME = os.environ["OPENSTACK_KEY_NAME"]
TEST_NETWORK = os.environ["OPENSTACK_NETWORK"]
TEST_BLOCK_STORAGE_SIZE = os.environ["OPENSTACK_BLOCK_STORAGE_SIZE"]
TEST_OPEN_PORTS = os.environ["OPENSTACK_OPEN_PORTS"]
TEST_USER_DATA = os.environ["OPENSTACK_USER_DATA"]
