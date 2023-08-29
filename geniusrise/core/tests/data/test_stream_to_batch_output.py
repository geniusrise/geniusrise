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

import os

import boto3
import pytest
from kafka import KafkaConsumer

from geniusrise.core.data import StreamToBatchOutput

# Constants
KAFKA_SERVERS = "localhost:9094"
OUTPUT_TOPIC = "test_batch_to_streaming_topic"
GROUP_ID = "test_group"
BUCKET = "geniusrise-test-bucket"
S3_FOLDER = "whatever"
BUFFER_SIZE = 10


# Fixtures
@pytest.fixture
def stream_to_batch_output_config(tmpdir):
    return StreamToBatchOutput(
        output_topic=OUTPUT_TOPIC,
        kafka_servers=KAFKA_SERVERS,
        output_folder=tmpdir,
        bucket=BUCKET,
        s3_folder=S3_FOLDER,
        buffer_size=BUFFER_SIZE,
    )


@pytest.fixture
def kafka_consumer():
    consumer = KafkaConsumer(OUTPUT_TOPIC, bootstrap_servers=KAFKA_SERVERS, group_id=GROUP_ID)
    consumer.commit()
    return consumer


# Helper function
def file_exists_in_s3(bucket, key):
    s3 = boto3.resource("s3")
    try:
        s3.Object(bucket, key).load()
    except Exception as e:
        return False
    return True


# Tests
def test_stream_to_batch_output_init(stream_to_batch_output_config):
    assert stream_to_batch_output_config.buffer_size == BUFFER_SIZE


def test_stream_to_batch_output_save(stream_to_batch_output_config):
    data = {"test": "data"}
    for _ in range(BUFFER_SIZE):
        stream_to_batch_output_config.save(data)

    files = os.listdir(stream_to_batch_output_config.output_folder)
    assert any(file_exists_in_s3(BUCKET, os.path.join(S3_FOLDER, f)) for f in files)


def test_stream_to_batch_output_flush(stream_to_batch_output_config):
    data = {"test": "data"}
    for _ in range(BUFFER_SIZE - 1):
        stream_to_batch_output_config.save(data)

    stream_to_batch_output_config.flush()
    assert len(stream_to_batch_output_config.buffered_messages) == 0
