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

import logging
import json
import threading
import time
from typing import Dict, List, Union, Optional, Iterator, Any, Callable

try:
    from confluent_kafka import Consumer, KafkaError, KafkaException, TopicPartition
    CONFLUENT_KAFKA_AVAILABLE = True
except ImportError:
    CONFLUENT_KAFKA_AVAILABLE = False

from .input import Input

# Define a type alias for Kafka message
KafkaMessage = Dict[str, Any]


class KafkaConnectionError(Exception):
    """❌ Custom exception for kafka connection problems."""


class StreamingInput(Input):
    r"""
    📡 **StreamingInput**: Manages streaming input data from Kafka and other streaming sources.

    Attributes:
        input_topic (str or List[str]): Kafka topic(s) to consume data from.
        kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
        group_id (str): Kafka consumer group ID.
        consumer (Consumer): Confluent Kafka consumer instance.
        running (bool): Flag to control the consumer polling thread.

    Usage:
        input = StreamingInput("my_topic", "localhost:9094")
        for message in input.get():
            print(message)

    Args:
        input_topic (str or List[str]): Kafka topic(s) to consume data from.
        kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
        group_id (str, optional): Kafka consumer group ID. Defaults to "geniusrise".
        **kwargs: Additional keyword arguments for Kafka Consumer.

    Raises:
        KafkaConnectionError: If unable to connect to Kafka.
        ImportError: If confluent_kafka is not installed.
    """

    __connectors__ = ["kafka"]

    def __init__(
        self,
        input_topic: Union[str, List[str]],
        kafka_cluster_connection_string: str,
        group_id: str = "geniusrise",
        **kwargs,
    ) -> None:
        """
        💥 Initialize a new streaming input from Kafka.

        Args:
            input_topic (str or List[str]): Kafka topic(s) to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
            **kwargs: Additional configuration for the Kafka consumer.
        """
        if not CONFLUENT_KAFKA_AVAILABLE:
            raise ImportError(
                "confluent-kafka is not installed. Install it with: pip install geniusrise[kafka]"
            )

        super().__init__()
        self.log = logging.getLogger(self.__class__.__name__)

        # Convert single topic to list for consistent handling
        if isinstance(input_topic, str):
            self.input_topic = [input_topic]
        else:
            self.input_topic = input_topic

        self.kafka_cluster_connection_string = kafka_cluster_connection_string
        self.group_id = group_id
        self.running = False
        self._messages_queue = []
        self._polling_thread = None
        self._metrics = {
            "messages_consumed": 0,
            "errors": 0,
            "last_poll_time": 0,
            "avg_poll_latency": 0,
        }

        # Configure consumer
        config = {
            'bootstrap.servers': self.kafka_cluster_connection_string,
            'group.id': self.group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': True,
            'max.poll.interval.ms': 600000,  # 10 minutes
            'session.timeout.ms': 30000,  # 30 seconds
        }

        # Add any additional configuration
        config.update(kwargs)

        try:
            self.consumer = Consumer(config)
            self.consumer.subscribe(self.input_topic)
            self.log.info(f"Connected to Kafka at {kafka_cluster_connection_string}, "
                         f"subscribed to topics: {self.input_topic}")
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka consumer: {e}")
            raise KafkaConnectionError(f"Failed to connect to Kafka: {e}")

    def __del__(self):
        self.close()

    def _start_polling(self):
        """Start a background thread to poll Kafka messages."""
        if self._polling_thread is not None and self._polling_thread.is_alive():
            return

        self.running = True
        self._polling_thread = threading.Thread(target=self._poll_messages, daemon=True)
        self._polling_thread.start()

    def _poll_messages(self):
        """Poll messages from Kafka in a background thread."""
        while self.running:
            try:
                start_time = time.time()
                msg = self.consumer.poll(1.0)  # Poll with 1 second timeout
                poll_latency = time.time() - start_time

                # Update metrics
                self._metrics["last_poll_time"] = time.time()
                self._metrics["avg_poll_latency"] = (
                    (self._metrics["avg_poll_latency"] * self._metrics["messages_consumed"] + poll_latency) /
                    (self._metrics["messages_consumed"] + 1)
                ) if self._metrics["messages_consumed"] > 0 else poll_latency

                if msg is None:
                    continue

                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        # End of partition, not an error
                        continue
                    else:
                        self.log.error(f"Kafka error: {msg.error()}")
                        self._metrics["errors"] += 1
                        continue

                # Process the message
                self._metrics["messages_consumed"] += 1

                # Convert message to a dict for easier handling
                message = {
                    'topic': msg.topic(),
                    'partition': msg.partition(),
                    'offset': msg.offset(),
                    'timestamp': msg.timestamp()[1],
                    'key': msg.key().decode('utf-8') if msg.key() else None,
                    'value': json.loads(msg.value().decode('utf-8')) if msg.value() else None,
                    'headers': msg.headers() if hasattr(msg, 'headers') else None,
                }

                self._messages_queue.append(message)

            except Exception as e:
                self.log.exception(f"Error while polling Kafka: {e}")
                self._metrics["errors"] += 1
                time.sleep(1)  # Avoid busy-waiting in case of errors

    def get(self) -> Iterator[KafkaMessage]:
        """
        📥 Get data from the input topic as an iterator.

        Yields:
            KafkaMessage: Dictionary containing message data (topic, partition, offset, key, value, etc.)

        Raises:
            KafkaConnectionError: If no Kafka consumer is available.
        """
        if not self.consumer:
            raise KafkaConnectionError("No Kafka consumer available.")

        self._start_polling()

        while True:
            while self._messages_queue:
                yield self._messages_queue.pop(0)

            # If no messages, yield control back to allow other operations
            time.sleep(0.1)

    def poll(self, timeout: float = 1.0) -> Optional[KafkaMessage]:
        """
        Poll a single message from Kafka with the specified timeout.

        Args:
            timeout: Timeout in seconds

        Returns:
            A message dictionary or None if no message is available
        """
        if not self.consumer:
            raise KafkaConnectionError("No Kafka consumer available.")

        try:
            msg = self.consumer.poll(timeout)

            if msg is None or msg.error():
                return None

            # Convert message to a dict for easier handling
            return {
                'topic': msg.topic(),
                'partition': msg.partition(),
                'offset': msg.offset(),
                'timestamp': msg.timestamp()[1],
                'key': msg.key().decode('utf-8') if msg.key() else None,
                'value': json.loads(msg.value().decode('utf-8')) if msg.value() else None,
                'headers': msg.headers() if hasattr(msg, 'headers') else None,
            }
        except Exception as e:
            self.log.exception(f"Error while polling Kafka: {e}")
            return None

    def compose(self, *inputs: "StreamingInput") -> Union[bool, str]:
        """
        Compose multiple StreamingInput instances by merging their topic subscriptions.

        Args:
            inputs (StreamingInput): Variable number of StreamingInput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.
        """
        try:
            # Validate that all inputs are of type StreamingInput
            for input_instance in inputs:
                if not isinstance(input_instance, StreamingInput):
                    return f"❌ Incompatible input type: {type(input_instance).__name__}"

            # Merge the topics from all the StreamingInput instances
            all_topics = list(self.input_topic)
            for input_instance in inputs:
                all_topics.extend(input_instance.input_topic)

            # Remove duplicates while preserving order
            unique_topics = []
            for topic in all_topics:
                if topic not in unique_topics:
                    unique_topics.append(topic)

            # Update subscription to all topics
            self.consumer.unsubscribe()
            self.consumer.subscribe(unique_topics)
            self.input_topic = unique_topics

            self.log.info(f"Updated Kafka subscription to topics: {unique_topics}")
            return True

        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            return str(e)

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer and stop the polling thread.
        """
        self.running = False

        if self._polling_thread and self._polling_thread.is_alive():
            self._polling_thread.join(timeout=2.0)

        if self.consumer:
            try:
                self.consumer.close()
                self.log.info("Kafka consumer closed successfully")
            except Exception as e:
                self.log.debug(f"🚫 Failed to close Kafka consumer: {e}")

    def seek(self, partition: int, offset: int) -> None:
        """
        Seek to a specific offset in a partition.

        Args:
            partition: The partition number
            offset: The offset to seek to

        Raises:
            KafkaConnectionError: If the seek operation fails
        """
        if not self.consumer:
            raise KafkaConnectionError("No Kafka consumer available.")

        try:
            # First, we need to ensure we're subscribed to the topics
            if not self.input_topic:
                raise KafkaConnectionError("No topics subscribed.")

            # Create a list of TopicPartition objects for the seek operation
            topic_partitions = []
            for topic in self.input_topic:
                tp = TopicPartition(topic, partition, offset)
                topic_partitions.append(tp)

            # Seek to the specified offset for all topics
            self.consumer.assign(topic_partitions)
            self.log.info(f"Seeked to offset {offset} in partition {partition} for topics {self.input_topic}")

        except Exception as e:
            raise KafkaConnectionError(f"Failed to seek Kafka consumer: {e}")

    def commit(self) -> None:
        """
        ✅ Manually commit offsets.

        Raises:
            KafkaConnectionError: If an error occurs while committing offsets.
        """
        if not self.consumer:
            raise KafkaConnectionError("No Kafka consumer available.")

        try:
            self.consumer.commit(asynchronous=False)
            self.log.info("Manually committed Kafka offsets")
        except Exception as e:
            raise KafkaConnectionError(f"🚫 Failed to commit offsets: {e}")

    def collect_metrics(self) -> Dict[str, Union[int, float]]:
        """
        📊 Collect metrics related to the Kafka consumer.

        Returns:
            Dict[str, Union[int, float]]: A dictionary containing metrics.
        """
        if not self.consumer:
            raise KafkaConnectionError("No Kafka consumer available.")

        # Return a copy of the metrics to avoid external modification
        return self._metrics.copy()
