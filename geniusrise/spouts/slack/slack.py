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

from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

from geniusrise.data_sources.batch import BatchDataFetcher
from geniusrise.data_sources.stream import StreamingDataFetcher


class SlackBatchDataFetcher(BatchDataFetcher):
    def __init__(self, token: str, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.client = WebClient(token=token)

    def fetch_all(self):
        """
        Fetch all historical data from all channels in the Slack workspace.
        """
        try:
            channels = self.client.conversations_list()["channels"]
            for channel in channels:
                self._fetch_channel(channel["id"])
            self.update_state("success")
        except Exception as e:
            self.log.error(f"Error fetching all channels: {e}")
            self.update_state("failure")

    def _fetch_channel(self, channel_id: str):
        """
        Fetch all historical data from a specific channel.

        :param channel_id: ID of the channel.
        """
        try:
            cursor = None
            while True:
                response = self.client.conversations_history(channel=channel_id, cursor=cursor)
                messages = response["messages"]
                self.save(messages, f"{channel_id}.json")
                cursor = response["response_metadata"]["next_cursor"]
                if not cursor:
                    break
        except Exception as e:
            self.log.error(f"Error fetching channel {channel_id}: {e}")


class SlackStreamingDataFetcher(StreamingDataFetcher):
    def __init__(self, token: str, app_token: str, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.client = WebClient(token=token)
        self.socket_mode_client = SocketModeClient(app_token=app_token)

    def listen(self):
        """
        Start the Socket Mode client and listen for new messages in all channels.
        """

        @self.socket_mode_client.socket_mode_request_listeners.add
        def handle_socket_mode_request(req: SocketModeRequest):
            if req.type == "events_api":
                event = req.payload["event"]
                if event["type"] == "message":
                    try:
                        self.save(event, f"{event['channel']}.json")
                        self.update_state("success")
                    except Exception as e:
                        self.log.error(f"Error saving message from channel {event['channel']}: {e}")
                        self.update_state("failure")
            return SocketModeResponse(envelope_id=req.envelope_id)

        self.socket_mode_client.connect()
