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

import asyncio

from aiokafka import AIOKafkaConsumer

from geniusrise.data_sources.stream import StreamingDataFetcher


class KafkaStreamingDataFetcher(StreamingDataFetcher):
    def __init__(self, bootstrap_servers: str, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.consumer = AIOKafkaConsumer(
            bootstrap_servers=bootstrap_servers,
            group_id="geniusrise",
            auto_offset_reset="earliest",
        )

    async def _event_loop_handler(self):
        """
        Start the Kafka consumer and listen for new messages in all topics.
        """
        await self.consumer.start()
        try:
            # Consume messages
            async for msg in self.consumer:
                try:
                    self.save(msg.value, f"{msg.topic}-{msg.partition}-{msg.offset}.json")
                    self.update_state("success")
                except Exception as e:
                    self.log.error(
                        f"Error saving message from topic {msg.topic}, partition {msg.partition}, offset {msg.offset}: {e}"
                    )
                    self.update_state("failure")
        finally:
            # Will leave consumer group; perform autocommit if enabled.
            await self.consumer.stop()

    def listen(self):
        """
        Start the asyncio event loop and the Kafka consumer.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self._event_loop_handler())
