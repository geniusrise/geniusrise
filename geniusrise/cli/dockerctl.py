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

import os
import subprocess
import logging
import argparse
import json
from rich_argparse import RichHelpFormatter
from typing import Optional
import boto3


class DockerCtl:
    r"""
    This class manages the creation and uploading of Docker containers.

    Attributes:
        base_image (str): The base image to use for the Docker container.
        workdir (str): The working directory in the Docker container.
        local_dir (str): The local directory to copy into the Docker container.
        packages (List[str]): List of packages to install in the Docker container.
        os_packages (List[str]): List of OS packages to install in the Docker container.
        env_vars (Dict[str, str]): Environment variables to set in the Docker container.

    Command-Line Interface:
        genius docker package <image_name> <repository> [options]

    Parameters:
        - <image_name>: The name of the Docker image to build and upload.
        - <repository>: The container repository to upload to (e.g., "ECR", "DockerHub", "Quay", "ACR", "GCR").

    Options:
        - --auth: Authentication credentials as a JSON string. Default is an empty JSON object.
        - --base_image: The base image to use for the Docker container. Default is "nvidia/cuda:12.2.0-runtime-ubuntu20.04".
        - --workdir: The working directory in the Docker container. Default is "/app".
        - --local_dir: The local directory to copy into the Docker container. Default is ".".
        - --packages: List of Python packages to install in the Docker container. Default is an empty list.
        - --os_packages: List of OS packages to install in the Docker container. Default is an empty list.
        - --env_vars: Environment variables to set in the Docker container. Default is an empty dictionary.

    Authentication Details:
        - ECR: `{"aws_region": "ap-south-1", "aws_secret_access_key": "aws_key", "aws_access_key_id": "aws_secret"}`
        - DockerHub: `{"dockerhub_username": "username", "dockerhub_password": "password"}`
        - ACR: `{"acr_username": "username", "acr_password": "password", "acr_login_server": "login_server"}`
        - GCR: `{"gcr_key_file_path": "/path/to/keyfile.json", "gcr_repository": "repository"}`
        - Quay: `{"quay_username": "username", "quay_password": "password"}`

    ## Examples

    #### Uploading to ECR (Amazon Elastic Container Registry)

    ```bash
    genius docker package geniusrise ecr --auth '{"aws_region": "ap-south-1"}'
    ```

    #### Uploading to DockerHub

    ```bash
    genius docker package geniusrise dockerhub --auth '{"dockerhub_username": "username", "dockerhub_password": "password"}'
    ```

    This is how we upload to dockerhub:

    ```bash
    export DOCKERHUB_USERNAME=
    export DOCKERHUB_PASSWORD=

    genius docker package geniusrise dockerhub \
        --packages geniusrise-listeners geniusrise-databases geniusrise-huggingface geniusrise-openai \
        --os_packages libmysqlclient-dev libldap2-dev libsasl2-dev libssl-dev
    ```

    ```bash
    genius docker package geniusrise-core dockerhub
    ```

    #### Uploading to ACR (Azure Container Registry)

    ```bash
    genius docker package geniusrise acr --auth '{"acr_username": "username", "acr_password": "password", "acr_login_server": "login_server"}'
    ```

    #### Uploading to GCR (Google Container Registry)

    ```bash
    genius docker package geniusrise gcr --auth '{"gcr_key_file_path": "/path/to/keyfile.json", "gcr_repository": "repository"}'
    ```

    """

    def __init__(self):
        """
        Initialize the DockerContainerManager with logging.
        """
        self.log = logging.getLogger(self.__class__.__name__)

    def create_parser(self, parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
        """
        Add arguments to the command-line parser for managing Docker containers.

        Args:
            parser (argparse.ArgumentParser): Command-line parser.

        Returns:
            argparse.ArgumentParser: The updated parser.
        """
        subparsers = parser.add_subparsers(dest="docker")

        # fmt: off
        build_upload_parser = subparsers.add_parser("package", help="Build and upload a Docker image.", formatter_class=RichHelpFormatter)
        build_upload_parser.add_argument("image_name", help="Name of the Docker image.", type=str)
        build_upload_parser.add_argument("repository", help="Container repository to upload to.", type=str)
        build_upload_parser.add_argument("--auth", help="Authentication credentials as a JSON string.", type=str, default="{}")
        build_upload_parser.add_argument("--base_image", help="The base image to use for the Docker container.", type=str, default="nvidia/cuda:12.2.0-runtime-ubuntu20.04")
        build_upload_parser.add_argument("--workdir", help="The working directory in the Docker container.", type=str, default="/app")
        build_upload_parser.add_argument("--local_dir", help="The local directory to copy into the Docker container.", type=str, default=".")
        build_upload_parser.add_argument("--packages", help="List of Python packages to install in the Docker container.", nargs="*", default=[])
        build_upload_parser.add_argument("--os_packages", help="List of OS packages to install in the Docker container.", nargs="*", default=[])
        build_upload_parser.add_argument("--env_vars", help="Environment variables to set in the Docker container.", type=json.loads, default={})
        # fmt: on

        return parser

    def run(self, args: argparse.Namespace) -> None:
        """
        Run the command-line interface.

        Args:
            args (argparse.Namespace): Parsed command-line arguments.
        """
        self.base_image = args.base_image
        self.workdir = args.workdir
        self.local_dir = args.local_dir
        self.packages = args.packages
        self.os_packages = args.os_packages
        self.env_vars = args.env_vars

        if args.docker == "package":
            self.log.info(f"Building and uploading Docker image: {args.image_name} to {args.repository}")

            # Create Dockerfile
            dockerfile_path = self.create_dockerfile()

            # Build Docker image
            build_success = self.build_image(args.image_name, dockerfile_path)
            if not build_success:
                self.log.error("Failed to build Docker image.")
                return

            # Upload to repository
            auth_dict = {}
            if args.auth:
                auth_dict = json.loads(args.auth)

            upload_success = self.upload_to_repository(args.image_name, args.repository, auth=auth_dict)
            if not upload_success:
                self.log.error("Failed to upload Docker image.")
                return

            self.log.info("Successfully built and uploaded Docker image.")
        else:
            self.log.error(f"Unrecognized command: {args.docker}")

    def create_dockerfile(self) -> str:
        """
        Create a Dockerfile based on the class attributes.

        Returns:
            str: The path to the created Dockerfile.
        """
        dockerfile_content = [
            f"FROM {self.base_image} AS base",
            "",
            f"WORKDIR {self.workdir}",
            "",
            # Set debconf to non-interactive mode
            "ENV DEBIAN_FRONTEND=noninteractive",
            # Create a non-root user and switch to it
            "RUN useradd --create-home genius",
            "",
            # Install Python 3.10
            "RUN apt-get update \\",
            " && apt-get install -y software-properties-common build-essential curl wget vim libpq-dev pkg-config \\",
            " && add-apt-repository ppa:deadsnakes/ppa \\",
            " && apt-get update \\",
            " && apt-get install -y python3.10 python3.10-dev python3.10-distutils \\",
            " && apt-get clean",
            # Install pip for Python 3.10
            "RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py \\",
            " && python3.10 get-pip.py",
            "",
        ]

        # Add OS package installation commands only if os_packages is not empty
        if self.os_packages:
            dockerfile_content.append(
                "RUN apt-get update && apt-get install -y \\" + " ".join(self.os_packages) + " && apt-get clean"
            )

        # Add Python package installation commands
        dockerfile_content.append("")
        for package in self.packages:
            dockerfile_content.append(f"RUN pip install {package}")
        dockerfile_content.append("RUN pip install --upgrade geniusrise")

        # Add environment variables
        for key, value in self.env_vars.items():
            dockerfile_content.append(f"ENV {key}={value}")
        dockerfile_content.append("ENV GENIUS=/home/genius/.local/bin/genius")

        # Add command to copy local directory to workdir
        dockerfile_content.append("")
        dockerfile_content.append(f"COPY --chown=genius:genius {self.local_dir} {self.workdir}/")

        # Install requirements
        dockerfile_content.append("")
        dockerfile_content.append("RUN pip3.10 install -r requirements.txt")

        # Dummy entrypoint
        dockerfile_content.append("USER genius")
        dockerfile_content.append("")
        dockerfile_content.append('CMD ["genius", "--help"]')

        dockerfile_path = "./Dockerfile"
        with open(dockerfile_path, "w") as f:
            f.write("\n".join(dockerfile_content))

        self.log.info(f"Dockerfile created at {dockerfile_path}")
        return dockerfile_path

    def build_image(self, image_name: str, dockerfile_path: str):
        """
        Build a Docker image based on the provided Dockerfile.

        Args:
            image_name (str): The name to give to the built Docker image.
            dockerfile_path (str): The path to the Dockerfile to use for building the image.

        Returns:
            bool: True if the build was successful, False otherwise.
        """
        try:
            subprocess.run(["docker", "build", "-t", image_name, "-f", dockerfile_path, "."], check=True)
            self.log.info(f"Successfully built Docker image: {image_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to build Docker image: {e}")
            return False

    def upload_to_repository(self, image_name: str, repository: str, auth: dict = {}) -> bool:
        """
        Upload the Docker image to a specified container repository.

        Args:
            image_name (str): The name of the Docker image to upload.
            repository (str): The container repository to upload to (e.g., "ECR", "DockerHub", "Quay").
            auth (dict, optional): Authentication credentials for the container repository. Defaults to None.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        if repository.lower() == "ecr":
            return self.upload_to_ecr(image_name=image_name, auth=auth)

        elif repository.lower() == "dockerhub":
            return self.upload_to_dockerhub(image_name=image_name, auth=auth)

        elif repository.lower() == "quay":
            return self.upload_to_quay(image_name=image_name, auth=auth)

        elif repository.lower() == "gcr":
            return self.upload_to_gcr(image_name=image_name, auth=auth)

        elif repository.lower() == "acr":
            return self.upload_to_acr(image_name=image_name, auth=auth)

        else:
            self.log.error(f"Unsupported repository: {repository}")
            return False

    def upload_to_ecr(self, image_name: str, auth: dict, ecr_repo: Optional[str] = None) -> bool:
        """
        Upload the Docker image to Amazon Elastic Container Registry (ECR).

        Args:
            image_name (str): The name of the Docker image to upload.
            auth (dict): Authentication credentials for ECR.
            ecr_repo (Optional[str]): The ECR repository to upload to. If not provided, it will be generated.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        aws_secret_access_key = auth.get("aws_secret_access_key", os.environ.get("AWS_SECRET_ACCESS_KEY"))
        aws_access_key_id = auth.get("aws_access_key_id", os.environ.get("AWS_ACCESS_KEY_ID"))
        aws_region = auth.get("aws_region", os.environ.get("AWS_DEFAULT_REGION"))

        sts_client = boto3.client(
            "sts",
            region_name=aws_region,
            aws_secret_access_key=aws_secret_access_key,
            aws_access_key_id=aws_access_key_id,
        )
        account_id = sts_client.get_caller_identity().get("Account")
        ecr_repo = f"{account_id}.dkr.ecr.{aws_region}.amazonaws.com"

        combined_command = f"""aws ecr get-login-password --region {aws_region} | docker login --username AWS --password-stdin {ecr_repo} &&
                            docker tag {image_name} {ecr_repo}/{image_name} &&
                            docker push {ecr_repo}/{image_name}"""

        try:
            subprocess.run(combined_command, shell=True, check=True)
            self.log.info(f"Successfully uploaded {image_name} to ECR repository {ecr_repo}")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to upload to ECR: {e}")
            return False

    def upload_to_acr(self, image_name: str, auth: dict) -> bool:
        """
        Upload the Docker image to Azure Container Registry (ACR).

        Args:
            image_name (str): The name of the Docker image to upload.
            auth (dict): Authentication credentials for ACR.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        acr_username = auth.get("acr_username", os.environ.get("ACR_USERNAME"))
        acr_password = auth.get("acr_password", os.environ.get("ACR_PASSWORD"))
        acr_login_server = auth.get("acr_login_server", os.environ.get("ACR_LOGIN_SERVER"))

        combined_command = f"""echo {acr_password} | docker login {acr_login_server} --username {acr_username} --password-stdin &&
                            docker tag {image_name} {acr_login_server}/{image_name} &&
                            docker push {acr_login_server}/{image_name}"""

        try:
            subprocess.run(combined_command, shell=True, check=True)
            self.log.info(f"Successfully uploaded {image_name} to ACR")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to upload to ACR: {e}")
            return False

    def upload_to_gcr(self, image_name: str, auth: dict) -> bool:
        """
        Upload the Docker image to Google Container Registry (GCR).

        Args:
            image_name (str): The name of the Docker image to upload.
            auth (dict): Authentication credentials for GCR.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        gcr_key_file_path = auth.get("gcr_key_file_path", os.environ.get("GCR_KEY_FILE_PATH"))
        gcr_repository = auth.get("gcr_repository", os.environ.get("GCR_REPOSITORY"))

        combined_command = f"""cat {gcr_key_file_path} | docker login -u _json_key --password-stdin https://{gcr_repository} &&
                            docker tag {image_name} {gcr_repository}/{image_name} &&
                            docker push {gcr_repository}/{image_name}"""

        try:
            subprocess.run(combined_command, shell=True, check=True)
            self.log.info(f"Successfully uploaded {image_name} to GCR")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to upload to GCR: {e}")
            return False

    def upload_to_dockerhub(self, image_name: str, auth: dict) -> bool:
        """
        Upload the Docker image to DockerHub.

        Args:
            image_name (str): The name of the Docker image to upload.
            auth (dict): Authentication credentials for DockerHub.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        dockerhub_username = auth.get("dockerhub_username") if auth else os.environ.get("DOCKERHUB_USERNAME")
        dockerhub_password = auth.get("dockerhub_password") if auth else os.environ.get("DOCKERHUB_PASSWORD")

        try:
            tag_command = f"docker tag {image_name} {dockerhub_username}/{image_name}"
            subprocess.run(tag_command, shell=True, check=True)

            # Authenticate Docker with DockerHub and Push the image in a single shell session
            combined_command = f"""echo {dockerhub_password} | docker login --username {dockerhub_username} --password-stdin &&
                                docker push {dockerhub_username}/{image_name}"""
            subprocess.run(combined_command, shell=True, check=True)

            self.log.info(f"Successfully uploaded {image_name} to DockerHub")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to upload to DockerHub: {e}")
            return False

    def upload_to_quay(self, image_name: str, auth: dict) -> bool:
        """
        Upload the Docker image to Quay.io.

        Args:
            image_name (str): The name of the Docker image to upload.
            auth (dict): Authentication credentials for Quay.io.

        Returns:
            bool: True if the upload was successful, False otherwise.
        """
        quay_username = auth.get("quay_username") if auth else os.environ.get("QUAY_USERNAME")
        quay_password = auth.get("quay_password") if auth else os.environ.get("QUAY_PASSWORD")
        try:
            # Authenticate Docker with Quay.io
            login_command = f"docker login quay.io --username {quay_username} --password {quay_password}"
            subprocess.run(login_command, shell=True, check=True)

            # Tag the image
            tag_command = f"docker tag {image_name} quay.io/{quay_username}/{image_name}"
            subprocess.run(tag_command, shell=True, check=True)

            # Push the image
            push_command = f"docker push quay.io/{quay_username}/{image_name}"
            subprocess.run(push_command, shell=True, check=True)

            self.log.info(f"Successfully uploaded {image_name} to Quay.io")
            return True
        except subprocess.CalledProcessError as e:
            self.log.error(f"Failed to upload to Quay.io: {e}")
            return False
