import redis  # type: ignore
import json
from typing import Optional, Callable
from data_sources.streaming import StreamingDataFetcher
from data_sources.state import StateManager


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
