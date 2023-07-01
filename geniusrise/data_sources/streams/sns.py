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
