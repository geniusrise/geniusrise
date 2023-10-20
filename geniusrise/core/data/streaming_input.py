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

import logging
from typing import Dict, List, Union, Generator, Any, Callable
from queue import Queue, Empty

from kafka import KafkaConsumer, TopicPartition
from pyspark.sql import DataFrame, Row
from pyspark.sql.streaming import StreamingQuery
from pyspark.rdd import RDD
from pyflink.table import Table
from pyflink.datastream import DataStream
from streamz.dataframe import DataFrame as ZDataFrame

from .input import Input

KafkaMessage = dict


class KafkaConnectionError(Exception):
    """❌ Custom exception for kafka connection problems."""


class StreamingInput(Input):
    r"""
    📡 **StreamingInput**: Manages streaming input data from Kafka and other streaming sources.

    Attributes:
        input_topic (str): Kafka topic to consume data from.
        kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
        group_id (str): Kafka consumer group ID.
        consumer (KafkaConsumer): Kafka consumer instance.

    Usage:
        input = StreamingInput("my_topic", "localhost:9094")
        for message in input.get():
            print(message.value)

    Args:
        input_topic (str): Kafka topic to consume data from.
        kafka_cluster_connection_string (str): Connection string for the Kafka cluster.
        group_id (str, optional): Kafka consumer group ID. Defaults to "geniusrise".
        **kwargs: Additional keyword arguments for KafkaConsumer.

    Raises:
        KafkaConnectionError: If unable to connect to Kafka.

    Usage:

        ### Using `get` method to consume from Kafka
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        consumer = input.get()
        for message in consumer:
            print(message.value)
        ```

        ### Using `from_streamz` method to process streamz DataFrame
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        streamz_df = ...  # Assume this is a streamz DataFrame
        for row in input.from_streamz(streamz_df):
            print(row)
        ```

        ### Using `from_spark` method to process Spark DataFrame
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        spark_df = ...  # Assume this is a Spark DataFrame
        map_func = lambda row: {"key": row.key, "value": row.value}
        query_or_rdd = input.from_spark(spark_df, map_func)
        ```

        ### Using `from_flink` method to process Flink Table
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        flink_table = ...  # Assume this is a Flink Table
        map_func = lambda row: {"key": row[0], "value": row[1]}
        data_stream = input.from_flink(flink_table, map_func)
        ```

        ### Using `compose` method to merge multiple StreamingInput instances
        ```python
        input1 = StreamingInput("topic1", "localhost:9094")
        input2 = StreamingInput("topic2", "localhost:9094")
        result = input1.compose(input2)
        ```

        ### Using `close` method to close the Kafka consumer
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        input.close()
        ```

        ### Using `seek` method to seek to a specific offset
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        input.seek(42)
        ```

        ### Using `commit` method to manually commit offsets
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        input.commit()
        ```

        ### Using `collect_metrics` method to collect Kafka metrics
        ```python
        input = StreamingInput("my_topic", "localhost:9094")
        metrics = input.collect_metrics()
        print(metrics)
        ```
    """

    def __init__(
        self,
        input_topic: Union[str, List[str]],
        kafka_cluster_connection_string: str,
        group_id: str = "geniusrise",
        **kwargs,
    ) -> None:
        """
        💥 Initialize a new streaming input data.

        Args:
            input_topic (str): Kafka topic to consume data.
            kafka_cluster_connection_string (str): Kafka cluster connection string.
            group_id (str, optional): Kafka consumer group id. Defaults to "geniusrise".
        """
        super(Input, self).__init__()
        self.log = logging.getLogger(self.__class__.__name__)
        self.input_topic = input_topic
        self.kafka_cluster_connection_string = kafka_cluster_connection_string
        self.group_id = group_id

        try:
            self.consumer = KafkaConsumer(
                self.input_topic,
                bootstrap_servers=self.kafka_cluster_connection_string,
                group_id=self.group_id,
                max_poll_interval_ms=600000,  # 10 minutes
                session_timeout_ms=10000,  # 10 seconds
                **kwargs,
            )
        except Exception as e:
            self.log.exception(f"🚫 Failed to create Kafka consumer: {e}")
            raise KafkaConnectionError("Failed to connect to Kafka.")

    def __del__(self):
        self.close()

    def get(self) -> KafkaConsumer:
        """
        📥 Get data from the input topic.

        Returns:
            KafkaConsumer: The Kafka consumer.

        Raises:
            Exception: If no input source or consumer is specified.
        """
        if self.input_topic and self.consumer:
            try:
                return self.consumer
            except Exception as e:
                self.log.exception(f"🚫 Failed to consume from Kafka topic {self.input_topic}: {e}")
                raise
        else:
            raise KafkaConnectionError("No Kafka consumer available.")

    def from_streamz(
        self, streamz_df: ZDataFrame, sentinel: Any = None, timeout: int = 5
    ) -> Generator[Any, None, None]:
        """
        Process a streamz DataFrame as a stream, similar to Kafka processing.

        Args:
            streamz_df (ZDataFrame): The streamz DataFrame to process.
            sentinel (Any): The value that, when received, will stop the generator.
            timeout (int): The time to wait for an item from the queue before raising an exception.

        Yields:
            Any: Yields each row as a dictionary.
        """
        q: Any = Queue()

        def enqueue(x):
            q.put(x)

        stream = streamz_df.stream
        stream.sink(enqueue)

        while True:
            try:
                item = q.get(timeout=timeout)
            except Empty:
                self.log.warn("Queue is empty.")
                continue

            if sentinel is not None and item.equals(sentinel.reset_index(drop=True)):
                break
            yield item

    def from_spark(self, spark_df: DataFrame, map_func: Callable[[Row], Any]) -> Union[StreamingQuery, RDD[Any]]:
        """
        Process a Spark DataFrame as a stream, similar to Kafka processing.

        Args:
            spark_df (DataFrame): The Spark DataFrame to process.
            map_func (Callable[[Row], Any]): Function to map each row of the DataFrame.

        Returns:
            Union[StreamingQuery, RDD[Any]]: Returns a StreamingQuery for streaming DataFrames, and an RDD for batch DataFrames.

        Raises:
            Exception: If an error occurs during processing.
        """
        try:
            if spark_df.isStreaming:
                return spark_df.writeStream.foreach(map_func).start()
            else:
                return spark_df.rdd.map(map_func)
        except Exception as e:
            self.log.exception(f"❌ Failed to process Spark DataFrame: {e}")
            raise

    def from_flink(self, flink_table: Table, map_func: Callable[[Row], Any]) -> DataStream:
        """
        Process a Flink Table as a stream, similar to Kafka processing.

        Args:
            flink_table (Table): The Flink Table to process.
            map_func (Callable[[Row], Any]): Function to map each row of the Table.

        Returns:
            DataStream: Returns a Flink DataStream after applying the map function.

        Raises:
            Exception: If an error occurs during processing.
        """
        try:
            # Apply the map function to the DataStream
            mapped_stream = flink_table.map(map_func)
            return mapped_stream
        except Exception as e:
            self.log.exception(f"❌ Failed to process Flink Table: {e}")
            raise

    def compose(self, *inputs: "StreamingInput") -> Union[bool, str]:  # type: ignore
        """
        Compose multiple StreamingInput instances by merging their iterators.

        Args:
            inputs (StreamingInput): Variable number of StreamingInput instances.

        Returns:
            Union[bool, str]: True if successful, error message otherwise.

        Caveat:
            On merging different topics, other operations such as
        """
        try:
            # Validate that all inputs are of type StreamingInput
            for input_instance in inputs:
                if not isinstance(input_instance, StreamingInput):
                    return f"❌ Incompatible input type: {type(input_instance).__name__}"

            # Merge the topics from all the StreamingInput instances
            all_topics = [self.input_topic] + [input_instance.input_topic for input_instance in inputs]

            # Create a new KafkaConsumer subscribed to all topics
            merged_consumer = KafkaConsumer(
                *all_topics,
                bootstrap_servers=self.kafka_cluster_connection_string,
                group_id=self.group_id,
                max_poll_interval_ms=600000,  # 10 minutes
                session_timeout_ms=10000,  # 10 seconds
            )

            # Replace the existing consumer with the new merged consumer
            self.consumer.close()
            self.consumer = merged_consumer
            self.input_topic = [t for t in all_topics if type(t) is str]  # store all the topics as a list

            return True
        except Exception as e:
            self.log.exception(f"❌ Error during composition: {e}")
            raise

    def close(self) -> None:
        """
        🚪 Close the Kafka consumer.

        Raises:
            Exception: If an error occurs while closing the consumer.
        """
        if self.consumer:
            try:
                self.consumer.close()
            except Exception as e:
                self.log.debug(f"🚫 Failed to close Kafka consumer: {e}")

    def seek(self, target_offset: int) -> None:
        if self.consumer and type(self.input_topic) is str:
            try:
                # Check if consumer is subscribed to the topic
                if not self.consumer.subscription():
                    raise KafkaConnectionError("Consumer is not subscribed to any topic.")

                # Get topic partitions
                partitions = self.consumer.partitions_for_topic(self.input_topic)

                # Check if partitions are assigned
                if not partitions:
                    raise KafkaConnectionError("No partitions are assigned to the consumer.")

                assigned_partitions = self.consumer.assignment()

                # Iterate through partitions to find the one with the target offset
                for partition in partitions:
                    tp = TopicPartition(self.input_topic, partition)

                    # Check if the partition is assigned
                    if tp not in assigned_partitions:
                        continue

                    beginning_offsets = self.consumer.beginning_offsets([tp])
                    end_offsets = self.consumer.end_offsets([tp])

                    if beginning_offsets[tp] <= target_offset <= end_offsets[tp]:
                        self.consumer.seek(tp, target_offset)
                        return

                raise Exception(f"Offset {target_offset} not found in any assigned partition.")

            except Exception as e:
                raise KafkaConnectionError(f"Failed to seek Kafka consumer: {e}")

    def commit(self) -> None:
        """
        ✅ Manually commit offsets.

        Raises:
            Exception: If an error occurs while committing offsets.
        """
        if self.consumer:
            try:
                self.consumer.commit()
            except Exception as e:
                raise KafkaConnectionError(f"🚫 Failed to commit offsets: {e}")

    def collect_metrics(self) -> Dict[str, Union[int, float]]:
        """
        📊 Collect metrics related to the Kafka consumer.

        Returns:
            Dict[str, Union[int, float]]: A dictionary containing metrics like latency.
        """
        if self.consumer:
            kafka_metrics = self.consumer.metrics()
            # Extract relevant latency metrics
            request_latency_avg = kafka_metrics.get("request-latency-avg", 0)
            request_latency_max = kafka_metrics.get("request-latency-max", 0)

            return {
                "request_latency_avg": request_latency_avg,
                "request_latency_max": request_latency_max,
            }
        else:
            raise KafkaConnectionError("No Kafka consumer available.")
