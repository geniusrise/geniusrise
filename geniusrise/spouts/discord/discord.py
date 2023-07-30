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

from typing import List, Union

import discord

from geniusrise.data_sources.batch import BatchDataFetcher
from geniusrise.data_sources.stream import StreamingDataFetcher


class DiscordDataFetcher(BatchDataFetcher):
    def __init__(self, token: str, guild_id: int, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.client = discord.Client()
        self.token = token
        self.guild_id = guild_id

    async def __fetch_guild(self):
        """
        Fetch all messages from all TextChannels and ForumChannels in the guild.
        """
        try:
            await self.client.wait_until_ready()
            guild = self.client.get_guild(self.guild_id)
            if not guild:
                self.log.error(f"Guild with ID {self.guild_id} not found.")
                return
            for channel in guild.channels:
                if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                    await self.__fetch_channel(channel)
            self.client.close()
        except Exception as e:
            self.log.error(f"Error fetching guild: {e}")
            self.update_state("failure")

    async def __fetch_channel(self, channel: Union[discord.TextChannel, discord.ForumChannel]):
        """
        Fetch all messages from a specific TextChannel or ForumChannel.

        :param channel: The TextChannel or ForumChannel to fetch messages from.
        """
        try:
            messages = await channel.history(limit=None).flatten()
            data = [message.content for message in messages]
            self.save(data, f"{channel.name}.json")
            self.update_state("success")
        except Exception as e:
            self.log.error(f"Error fetching channel {channel.name}: {e}")
            self.update_state("failure")

    def fetch_guild(self):
        """
        Start the Discord client and fetch all messages from the guild.
        """
        self.client.loop.create_task(self.fetch_guild())
        self.client.run(self.token)


class DiscordStreamingDataFetcher(StreamingDataFetcher):
    def __init__(self, token: str, channel_ids: List[int], handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.client = discord.Client()
        self.token = token
        self.channel_ids = channel_ids

    async def on_message(self, message):
        """
        Event that triggers when a message is sent in any of the channels that the bot has access to.

        :param message: The message that was sent.
        """
        if message.channel.id in self.channel_ids:
            try:
                data = message.content
                self.save(data, f"{message.channel.name}.json")
                self.update_state("success")
            except Exception as e:
                self.log.error(f"Error saving message from channel {message.channel.name}: {e}")
                self.update_state("failure")

    def listen(self):
        """
        Start the Discord client and listen for new messages in the specified channels.
        """
        self.client.event(self.on_message)
        self.client.run(self.token)
