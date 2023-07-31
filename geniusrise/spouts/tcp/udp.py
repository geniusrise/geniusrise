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

import socket

from geniusrise.data_sources.streaming import StreamingDataFetcher


class UdpDataFetcher(StreamingDataFetcher):
    def __init__(self, handler=None, state_manager=None, host: str = "localhost", port: int = 12345):
        super().__init__(handler, state_manager)
        self.host = host
        self.port = port

    def listen(self):
        """
        Start listening for data from the UDP server.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.bind((self.host, self.port))
            while True:
                data, addr = s.recvfrom(1024)
                self.save(data, "udp.json")
                self.update_state("success")
