import asyncio

import websockets

from geniusrise.data_sources.streaming import StreamingDataFetcher


class WebSocketDataFetcher(StreamingDataFetcher):
    def __init__(self, handler=None, state_manager=None, host: str = "localhost", port: int = 8765):
        super().__init__(handler, state_manager)
        self.host = host
        self.port = port

    async def __listen(self):
        """
        Start listening for data from the WebSocket server.
        """
        async with websockets.serve(self.receive_message, self.host, self.port):
            await asyncio.Future()  # run forever

    async def receive_message(self, websocket, path):
        """
        Receive a message from a WebSocket client and save it.

        :param websocket: WebSocket client connection.
        :param path: WebSocket path.
        """
        data = await websocket.recv()
        self.save(data, "websocket.json")
        self.update_state("success")

    def listen(self):
        """
        Start the WebSocket server.
        """
        self.__listen()
        asyncio.run(self.__listen())
