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
import json

from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.asyncio.server import serve
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import StreamDataReceived

from geniusrise.data_sources.streaming import StreamingDataFetcher


class QuicDataFetcher(StreamingDataFetcher):
    def __init__(self, cert_path: str, key_path: str, handler=None, state_manager=None, port: int = 4433):
        super().__init__(handler, state_manager)
        self.port = port
        self.cert_path = cert_path
        self.key_path = key_path

    async def handle_stream_data(self, data: bytes, stream_id: int):
        """
        Handle incoming stream data.

        :param data: The incoming data.
        :param stream_id: The ID of the stream.
        """
        data = json.loads(data.decode())
        self.save(data, f"stream_{stream_id}.json")
        self.update_state("success")

    async def handle_quic_event(self, event):
        """
        Handle a QUIC protocol event.

        :param event: The event to handle.
        """
        if isinstance(event, StreamDataReceived):
            await self.handle_stream_data(event.data, event.stream_id)

    def listen(self):
        """
        Start listening for data from the QUIC server.
        """
        configuration = QuicConfiguration(is_client=False)
        configuration.load_cert_chain(self.cert_path, self.key_path)

        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(
            serve(
                self.port,
                configuration=configuration,
                create_protocol=QuicConnectionProtocol,
                protocol_factory=self.handle_quic_event,
                loop=loop,
            )
        )

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.close()
            loop.run_until_complete(server.wait_closed())
            loop.close()
