# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import List

import boto3


def create_presigned_urls(bucket_name: str, prefix: str) -> List[str]:
    """
    Generate presigned URLs for all files in a specific S3 folder.

    :param bucket_name: Name of the S3 bucket
    :param prefix: The common prefix of all keys you want to match, effectively a folder path in S3
    :return: List of URLs
    """
    # Create a session using your AWS credentials
    s3_client = boto3.client("s3")
    presigned_urls = []

    # List objects within a given prefix
    response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
    for content in response.get("Contents", []):
        # Generate a presigned URL for each object
        url = s3_client.generate_presigned_url(
            "get_object", Params={"Bucket": bucket_name, "Key": content["Key"]}, ExpiresIn=86400
        )  # Link valid for 1 day
        presigned_urls.append(url)

    return presigned_urls


def send_email(
    recipient: str, bucket_name: str, prefix: str, from_email: str = "Geniusrise <mailer@geniusrise.ai>"
) -> None:
    """
    Send a nicely formatted email with the list of downloadable links.

    :param recipient: Email address to send the links to
    :param links: List of presigned URLs
    :param from_email: The email address sending this email
    """
    ses_client = boto3.client("ses")

    links = create_presigned_urls(bucket_name=bucket_name, prefix=prefix)

    # Email body
    body_html = """
    <html>
        <head></head>
        <body>
            <h1>🧠 Your Download Links from Geniusrise</h1>
            <p>We've prepared the files you requested. Below are the links to download them:</p>
            <ul>
    """
    for link in links:
        body_html += f"<li><a href='{link}'>⬇️ Download Link</a></li>"

    body_html += """
            </ul>
            <p>Please note that these links are <strong>valid for 24 hours only</strong>.</p>
            <p>Thank you for using <a href='https://geniusrise.com'>Geniusrise</a>!</p>
        </body>
    </html>
    """

    # Sending the email
    try:
        response = ses_client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "🧠 Your Download Links from Geniusrise"},
                "Body": {"Html": {"Data": body_html}},
            },
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"An error occurred: {e}")


def send_fine_tuning_email(
    recipient: str, bucket_name: str, prefix: str, from_email: str = "Geniusrise <mailer@geniusrise.ai>"
) -> None:
    """
    Send a nicely formatted email with the list of downloadable links.

    :param recipient: Email address to send the links to
    :param links: List of presigned URLs
    :param from_email: The email address sending this email
    """
    ses_client = boto3.client("ses")

    links = create_presigned_urls(bucket_name=bucket_name, prefix=prefix)

    # Email body
    body_html = """
    <html>
        <head></head>
        <body>
            <h1>🧠 Your Fine-Tuned Model Download Links from Geniusrise</h1>
            <p>We've prepared the models you requested. Below are the links to download them:</p>
            <ul>
    """
    for link in links:
        body_html += f"<li><a href='{link}'>⬇️ Download Link</a></li>"

    body_html += """
            </ul>
            <p>Please note that these links are <strong>valid for 24 hours only</strong>.</p>
            <p>Thank you for using <a href='https://geniusrise.com'>Geniusrise</a>!</p>
        </body>
    </html>
    """

    # Sending the email
    try:
        response = ses_client.send_email(
            Source=from_email,
            Destination={"ToAddresses": [recipient]},
            Message={
                "Subject": {"Data": "🧠 Your Fine-Tuned Model Download Links from Geniusrise"},
                "Body": {"Html": {"Data": body_html}},
            },
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"An error occurred: {e}")
