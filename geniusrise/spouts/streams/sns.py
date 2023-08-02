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

import logging
from typing import Callable, Optional

import boto3
from botocore.exceptions import ClientError
from streaming_data_fetcher import StreamingDataFetcher


class SNSDataFetcher(StreamingDataFetcher):
    """
    A class that fetches data from AWS SNS.
    """

    def __init__(self, handler: Optional[Callable] = None, state_manager=None):
        """
        Initialize the SNSDataFetcher class.

        :param handler: A callable function to handle the fetched data.
        :param state_manager: An instance of a state manager.
        """
        super().__init__(handler, state_manager)
        self.log = logging.getLogger(__name__)
        self.sns = boto3.resource("sns")

    async def listen(self):
        """
        Start listening for data from AWS SNS.
        """
        try:
            for topic in self.sns.topics.all():
                for subscription in topic.subscriptions.all():
                    self.log.info(f"Listening to topic {topic.arn} with subscription {subscription.arn}")
                    await self.__listen(subscription)
        except ClientError as e:
            self.log.error(f"Error listening to AWS SNS: {e}")
            self.update_state("failure")

    async def __listen(self, subscription):
        """
        Listen to a specific subscription.

        :param subscription: The subscription to listen to.
        """
        try:
            while True:
                messages = subscription.get_messages()
                for message in messages:
                    self.save(message, f"{subscription.arn}.json")
                    self.update_state("success")
        except ClientError as e:
            self.log.error(f"Error listening to subscription {subscription.arn}: {e}")
            self.update_state("failure")
