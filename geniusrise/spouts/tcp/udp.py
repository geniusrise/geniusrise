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
