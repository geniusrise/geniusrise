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
import logging
from typing import Callable, Optional

import aioredis

from geniusrise.data_sources.streaming_data_fetcher import StreamingDataFetcher


class RedisStreamDataFetcher(StreamingDataFetcher):
    """
    A class that fetches data from Redis Streams.
    """

    def __init__(self, redis_host: str, stream_key: str, handler: Optional[Callable] = None, state_manager=None):
        """
        Initialize the RedisStreamDataFetcher.

        :param redis_host: The host address of the Redis server.
        :param stream_key: The key of the Redis stream to fetch data from.
        :param handler: A function to handle the fetched data.
        :param state_manager: An instance of a state manager.
        """
        super().__init__(handler, state_manager)
        self.redis_host = redis_host
        self.stream_key = stream_key
        self.log = logging.getLogger(__name__)

    async def listen(self):
        """
        Start listening for data from the Redis stream.
        """
        try:
            self.log.info(f"Starting to listen to Redis stream {self.stream_key} on host {self.redis_host}")
            self.update_state("listening")

            redis = await aioredis.create_redis(self.redis_host)
            while True:
                result = await redis.xread([self.stream_key], timeout=1000)
                for _, message in result:
                    msg_id, fields = message
                    data = {k.decode(): v.decode() for k, v in fields.items()}
                    self.save(data, f"{self.stream_key}-{msg_id.decode()}.json")
                await asyncio.sleep(1)  # to prevent high CPU usage

        except Exception as e:
            self.log.error(f"Error while listening to Redis stream: {e}")
            self.update_state("error")
        finally:
            self.update_state("stopped")
            redis.close()
            await redis.wait_closed()

    def start_listening(self):
        """
        Start the asyncio event loop to listen for data from the Redis stream.
        """
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.listen())
