# geniusrise
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
from typing import List

from kiteconnect import KiteConnect, KiteTicker

from geniusrise.data_sources.streaming import StreamingDataFetcher


class ZerodhaStockTickerDataFetcher(StreamingDataFetcher):
    def __init__(self, api_key: str, access_token: str, instrument_tokens: List[int], handler=None, state_manager=None):
        """
        Initialize ZerodhaStockTickerDataFetcher with API key, access token, and instrument tokens.

        :param api_key: API key provided by Zerodha.
        :param access_token: Access token for the Zerodha API.
        :param instrument_tokens: List of instrument tokens to subscribe to.
        :param handler: Optional handler function to process the data.
        :param state_manager: Optional state manager to manage the state of the fetcher.
        """
        super().__init__(handler, state_manager)
        self.log = logging.getLogger(__name__)
        self.kite = KiteConnect(api_key=api_key)
        self.kite.set_access_token(access_token)
        self.ticker = KiteTicker(api_key, access_token)
        self.instrument_tokens = instrument_tokens

    def on_ticks(self, ws, ticks):
        """
        Callback to receive live market data.

        :param ws: WebSocket instance.
        :param ticks: List of tick data.
        """
        try:
            self.save(ticks, "zerodha_ticker.json")
            self.update_state("success")
        except Exception as e:
            self.log.error(f"Error saving tick data: {e}")
            self.update_state("failure")

    def on_connect(self, ws, response):
        """
        Callback on successful connect. Subscribe to the instruments.

        :param ws: WebSocket instance.
        :param response: Response from the server.
        """
        try:
            ws.subscribe(self.instrument_tokens)
        except Exception as e:
            self.log.error(f"Error subscribing to instruments: {e}")

    def on_close(self, ws, code, reason):
        """
        Callback on connection close.

        :param ws: WebSocket instance.
        :param code: Close code.
        :param reason: Close reason.
        """
        self.log.info(f"WebSocket closed with code {code}: {reason}")
        self.update_state("failure")

    def listen(self):
        """
        Start listening for data from the Zerodha WebSocket.
        """
        # Assign the callbacks.
        self.ticker.on_ticks = self.on_ticks
        self.ticker.on_connect = self.on_connect
        self.ticker.on_close = self.on_close

        try:
            # Infinite loop on the main thread. Nothing after this will run.
            self.ticker.run()
        except Exception as e:
            self.log.error(f"Error in WebSocket connection: {e}")
