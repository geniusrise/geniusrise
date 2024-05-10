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
import time

from kafka import KafkaProducer

test_topic = "test_topic"
kafka_cluster_connection_string = "localhost:9094"

producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)

for _ in range(60 * 10):
    producer.send(test_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
    time.sleep(1)
    producer.flush()
