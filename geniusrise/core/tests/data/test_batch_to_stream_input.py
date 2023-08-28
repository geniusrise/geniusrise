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
import os
from geniusrise.core.data import BatchToStreamingInput
from geniusrise.core.data.batch_to_stream_input import KafkaMessage

# Constants
KAFKA_CLUSTER_CONNECTION_STRING = "localhost:9094"
GROUP_ID = "test_group_1"
INPUT_TOPIC = "test_topic"
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "whatever"


# Fixture for BatchToStreamingInput
@pytest.fixture
def batch_to_streaming_input_config(tmpdir):
    return BatchToStreamingInput(
        input_topic=INPUT_TOPIC,
        kafka_cluster_connection_string=KAFKA_CLUSTER_CONNECTION_STRING,
        input_folder=str(tmpdir),
        bucket=BUCKET,
        s3_folder=S3_FOLDER,
        group_id=GROUP_ID,
    )


# Test Initialization
def test_batch_to_streaming_input_config_init(batch_to_streaming_input_config, tmpdir):
    assert batch_to_streaming_input_config.input_folder == str(tmpdir)


# Test stream_batch
def test_batch_to_streaming_input_config_stream_batch(batch_to_streaming_input_config, tmpdir):
    # Create a sample batch file
    sample_data = [{"key": i} for i in range(10)]
    for i, data in enumerate(sample_data):
        sample_file_path = tmpdir.join(f"sample-{i}.json")
        with open(sample_file_path, "w") as f:
            json.dump(data, f)

    # Test get method
    stream_iterator = batch_to_streaming_input_config.get()
    for _, kafka_message in enumerate(stream_iterator):
        assert kafka_message.value["key"] >= 0
        assert kafka_message.value["key"] < 10
        assert kafka_message.key is None


# Test KafkaMessage namedtuple
def test_kafka_message_namedtuple(batch_to_streaming_input_config):
    # Create a sample batch file
    sample_data = [{"key": 0}]
    sample_file_path = os.path.join(batch_to_streaming_input_config.input_folder, "sample.json")
    with open(sample_file_path, "w") as f:
        json.dump(sample_data, f)

    # Test get method
    stream_iterator = batch_to_streaming_input_config.get()
    kafka_message = next(stream_iterator)
    assert isinstance(kafka_message, KafkaMessage)
    assert kafka_message._fields == ("key", "value")
