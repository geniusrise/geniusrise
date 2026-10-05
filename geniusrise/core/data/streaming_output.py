# 🧠 Geniusrise
# Copyright (C) 2023-2025  geniusrise.ai
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
import logging
import time
from typing import Any, Dict, Union, Optional

try:
    from confluent_kafka import Producer
    CONFLUENT_KAFKA_AVAILABLE = True
except ImportError:
    CONFLUENT_KAFKA_AVAILABLE = False

from .output import Output


class KafkaConnectionError(Exception):
    """❌ Custom exception for kafka connection problems."""


class StreamingOutput(Output):
    """
    📡 **StreamingOutput**: Manages streaming output data to Kafka.

    Attributes:
        output_topic (str): Kafka topic to send data to.
        producer (Producer): Confluent Kafka producer for sending data.

    Usage:
    ```python
    output = StreamingOutput("my_topic", "localhost:9094")
    output.save({"key": "value"})
    output.flush()
    ```

    Args:
        output_topic (str): Kafka topic to send data to.
        kafka_servers (str): Kafka bootstrap servers (comma-separated list).
        **kwargs: Additional configuration for the Kafka producer.

    Raises:
        ImportError: If confluent_kafka is not installed.
        KafkaConnectionError: If unable to connect to Kafka.
    """

    __connectors__ = ["kafka"]

    def __init__(self, output_topic: str, kafka_servers: str, **kwargs) -> None:
        """
        Initialize a new streaming output to Kafka.

        Args:
            output_topic (str): Kafka topic to send data to.
            kafka_servers (str): Kafka bootstrap servers (comma-separated list).
            **kwargs: Additional configuration for the Kafka producer.
        """
        if not CONFLUENT_KAFKA_AVAILABLE:
            raise ImportError(
                "confluent-kafka is not installed. Install it with: pip install geniusrise[kafka]"
            )

        super().__init__()
        self.output_topic = output_topic
        self.log = logging.getLogger(self.__class__.__name__)
        self._metrics = {
            "messages_sent": 0,
            "errors": 0,
            "last_send_time": 0,
        }

        # Configure producer
        config = {
            'bootstrap.servers': kafka_servers,
            'client.id': f'geniusrise-producer-{int(time.time())}',
            # Default configuration for reliability
            'acks': 'all',               # Wait for all replicas
            'retries': 5,                # Retry up to 5 times
            'retry.backoff.ms': 200,     # Backoff between retries
        }

        # Add any additional configuration
        config.update(kwargs)

        try:
            self.producer = Producer(config)
            self.log.info(f"Connected to Kafka at {kafka_servers}, ready to produce to topic: {output_topic}")
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka producer: {e}")
            raise KafkaConnectionError(f"Failed to connect to Kafka: {e}")

    def __del__(self):
        self.close()

    def _delivery_callback(self, err, msg):
        """Callback function for producer delivery reports."""
        if err is not None:
            self.log.error(f'Message delivery failed: {err}')
            self._metrics["errors"] += 1
        else:
            self._metrics["messages_sent"] += 1
            self.log.debug(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

    def save(self, data: Any, key: Optional[str] = None, **kwargs) -> None:
        """
        📤 Send data to the Kafka topic.

        Args:
            data (Any): The data to send (will be JSON-serialized).
            key (Optional[str]): Optional message key.
            **kwargs: Additional keyword arguments (ignored).

        Raises:
            KafkaConnectionError: If no Kafka producer is available or an error occurs.
        """
        if not self.producer:
            raise KafkaConnectionError("No Kafka producer available.")

        try:
            # Convert data to JSON string, then to bytes
            value = json.dumps(data).encode('utf-8')

            # Record metrics
            self._metrics["last_send_time"] = time.time()

            # If key is provided, encode it too
            if key:
                key = str(key).encode('utf-8')

            # Send the message
            self.producer.produce(
                self.output_topic,
                value=value,
                key=key,
                callback=self._delivery_callback
            )

            # Poll to handle any callbacks
            self.producer.poll(0)

            self.log.debug(f"✅ Sent data to {self.output_topic} topic")

        except Exception as e:
            self._metrics["errors"] += 1
            self.log.exception(f"🚫 Failed to send data to Kafka topic: {e}")
            raise KafkaConnectionError(f"Failed to send data to Kafka: {e}")

    def flush(self, timeout: float = 10.0) -> None:
        """
        🔄 Flush the Kafka producer to ensure all messages are sent.

        Args:
            timeout (float): Timeout in seconds for the flush operation.

        Raises:
            KafkaConnectionError: If no Kafka producer is available.
        """
        if not self.producer:
            raise KafkaConnectionError("No Kafka producer available.")

        try:
            remaining_msgs = self.producer.flush(timeout=timeout)
            if remaining_msgs > 0:
                self.log.warning(f"Failed to flush all messages. {remaining_msgs} messages remaining.")
            else:
                self.log.info("All messages flushed successfully")
        except Exception as e:
            self.log.exception(f"🚫 Error during flush: {e}")
            raise KafkaConnectionError(f"Failed to flush Kafka producer: {e}")

    def close(self) -> None:
        """
        🚪 Close the Kafka producer.
        """
        if self.producer:
            try:
                # Flush any remaining messages before closing
                self.producer.flush()
                self.producer = None
                self.log.info("Kafka producer closed successfully")
            except Exception as e:
                self.log.debug(f"🚫 Could not close Kafka connection: {e}")

    def save_to_partition(self, data: Any, partition: int, key: Optional[str] = None) -> None:
        """
        🎯 Send data to a specific partition in the Kafka topic.

        Args:
            data (Any): The data to send (will be JSON-serialized).
            partition (int): The partition to send to.
            key (Optional[str]): Optional message key.

        Raises:
            KafkaConnectionError: If no Kafka producer is available or an error occurs.
        """
        if not self.producer:
            raise KafkaConnectionError("No Kafka producer available.")

        try:
            # Convert data to JSON string, then to bytes
            value = json.dumps(data).encode('utf-8')

            # If key is provided, encode it too
            if key:
                key = str(key).encode('utf-8')

            # Send the message to the specified partition
            self.producer.produce(
                topic=self.output_topic,
                value=value,
                key=key,
                partition=partition,
                callback=self._delivery_callback
            )

            # Poll to handle any callbacks
            self.producer.poll(0)

            self.log.debug(f"✅ Sent data to partition {partition} of {self.output_topic} topic")

        except Exception as e:
            self._metrics["errors"] += 1
            self.log.exception(f"🚫 Failed to send data to Kafka partition {partition}: {e}")
            raise KafkaConnectionError(f"Failed to send data to Kafka partition {partition}: {e}")

    def collect_metrics(self) -> Dict[str, Union[int, float]]:
        """
        📊 Collect metrics related to the Kafka producer.

        Returns:
            Dict[str, Union[int, float]]: A dictionary containing metrics.
        """
        if not self.producer:
            raise KafkaConnectionError("No Kafka producer available.")

        # Return a copy of the metrics to avoid external modification
        return self._metrics.copy()
