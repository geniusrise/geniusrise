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

import time
from kafka import KafkaProducer
import json

test_topic = "test_topic"
kafka_cluster_connection_string = "localhost:9094"

producer = KafkaProducer(bootstrap_servers=kafka_cluster_connection_string)

for _ in range(60 * 10):
    producer.send(test_topic, value=json.dumps({"test": "buffer"}).encode("utf-8"))
    time.sleep(1)
    producer.flush()
