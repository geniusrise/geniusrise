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

import json
from typing import Callable, Optional

import redis  # type: ignore
from data_sources.state import StateManager
from data_sources.streaming import StreamingDataFetcher


class RedisPubsubDataFetcher(StreamingDataFetcher):
    def __init__(
        self,
        host: str,
        port: int,
        channel: str,
        handler: Optional[Callable] = None,
        state_manager: Optional[StateManager] = None,
    ):
        super().__init__(handler, state_manager)
        self.host = host
        self.port = port
        self.channel = channel
        self.redis = redis.Redis(host=self.host, port=self.port, decode_responses=True)

    async def listen(self):
        pubsub = self.redis.pubsub()
        pubsub.subscribe(self.channel)

        self.log.info(f"Listening to channel {self.channel} on Redis server at {self.host}:{self.port}")

        try:
            for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    self.save(data, f"redis_{self.channel}.json")
                    self.update_state("success")
        except Exception as e:
            self.log.error(f"Error while listening to channel {self.channel}: {e}")
            self.update_state("failure")
