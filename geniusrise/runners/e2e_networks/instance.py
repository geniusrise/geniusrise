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

import requests
import logging
from argparse import ArgumentParser, Namespace
from typing import Optional
from rich import print_json


class E2EInstanceRunner:
    r"""
    🚀 Initialize the E2EInstanceRunner class for managing E2E instances.

    CLI Usage:
        genius e2e [sub-command] [options]
        Examples:

        ```bash
        genius e2e create --name example-instance --image Ubuntu-20.04 --plan C1.1GB --ssh-keys "ssh-key1,ssh-key2" \
            --open-ports "80,443" --tags "tag1,tag2" --region ncr --backup \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

        ```bash
        genius e2e get --node-id <node-id> \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

        ```bash
        genius e2e list \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

        ```bash
        genius e2e delete --node-id <node-id> \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

    YAML Configuration:

    ```yaml
    version: "1.0"
    instances:
        - name: "example-instance"
        image: "Ubuntu-20.04"
        plan: "C1.1GB"
        ssh_keys: "ssh-key1,ssh-key2"
        open_ports: "80,443"
        tags: "tag1,tag2"
        region: "ncr"
        backup: true
        api_key: "<api-key>"
        project_id: "<project-id>"
        location: "Delhi"
    ```
    """

    def __init__(self):
        """
        🚀 Initialize the E2EInstanceRunner class for managing E2E instances.
        """
        self.api_key: str = ""
        self.project_id: str = ""
        self.location: str = ""
        self.base_url: str = "https://api.e2enetworks.com/myaccount/api/v1"
        self.headers: dict = {}
        self.log = logging.getLogger(self.__class__.__name__)

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🛠 Add common connection arguments to a parser.

        Args:
            parser (ArgumentParser): The parser to which arguments will be added.

        Returns:
            ArgumentParser: The parser with added arguments.
        """
        parser.add_argument("--api-key", help="API key for E2E Networks.", type=str, required=True)
        parser.add_argument("--project-id", help="Project ID for E2E Networks.", type=str, required=True)
        parser.add_argument("--location", help="Location for E2E Networks.", type=str, required=True)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to E2E instance functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="e2e")

        # fmt: off
        create_parser = subparsers.add_parser("create", help="Create a new instance.")
        create_parser.add_argument("name", help="Name of the instance.", type=str)
        create_parser.add_argument("image", help="Image ID or name.", type=str)
        create_parser.add_argument("plan", help="Plan ID.", type=str)
        create_parser.add_argument("--ssh-keys", help="SSH keys for the instance (comma-separated).", type=str)
        create_parser.add_argument("--open-ports", help="Ports to be opened for the instance (comma-separated).", type=str)
        create_parser.add_argument("--tags", help="Tags for the instance (comma-separated).", type=str)
        create_parser.add_argument("--region", help="Region for the instance.", type=str, default="ncr")
        create_parser.add_argument("--backup", help="Enable backups for the instance.", action="store_true")
        create_parser = self._add_connection_args(create_parser)

        get_parser = subparsers.add_parser("get", help="Get details of an instance.")
        get_parser.add_argument("node_id", help="ID of the instance.", type=str)
        get_parser = self._add_connection_args(get_parser)

        list_parser = subparsers.add_parser("list", help="List instances.")
        list_parser = self._add_connection_args(list_parser)

        delete_parser = subparsers.add_parser("delete", help="Delete an instance.")
        delete_parser.add_argument("node_id", help="ID of the instance.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the E2E instance manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """
        self.api_key = args.api_key
        self.project_id = args.project_id
        self.location = args.location
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if args.e2e == "create":
            ssh_keys = args.ssh_keys.split(",") if args.ssh_keys else []
            open_ports = args.open_ports.split(",") if args.open_ports else []
            tags = args.tags.split(",") if args.tags else []
            self.create_node(args.name, args.image, args.plan, ssh_keys, open_ports, tags, args.region, args.backup)
        elif args.e2e == "get":
            self.get_node(args.node_id)
        elif args.e2e == "list":
            self.list_nodes()
        elif args.e2e == "delete":
            self.delete_node(args.node_id)
        else:
            raise ValueError(f"Unknown command: {args.e2e}")

    def create_security_group(self, name: str, open_ports: list) -> int:
        """
        🔒 Create a security group with the specified open ports.

        Args:
            name (str): The name of the security group.
            open_ports (list): The list of ports to open.

        Returns:
            int: The ID of the created security group.
        """
        url = f"{self.base_url}/security_group/?apikey={self.api_key}&contact_person_id=null&location={self.location}&project_id={self.project_id}"
        payload = {
            "name": name,
            "description": "",
            "rules": [
                {
                    "network": "any",
                    "rule_type": "Inbound",
                    "protocol_name": "Custom_TCP",
                    "port_range": ",".join(open_ports),
                },
                {"network": "any", "rule_type": "Outbound", "protocol_name": "All", "port_range": "All"},
            ],
            "default": False,
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        self.log.info(f"🔐 Created security group {name} with ID {data['data']['resource_type']}")
        return data["data"]["resource_type"]

    def create_node(
        self,
        name: str,
        image: str,
        plan: str,
        ssh_keys: Optional[list] = None,
        open_ports: Optional[list] = None,
        tags: Optional[list] = None,
        region: str = "ncr",
        backup: bool = False,
        **kwargs,
    ):
        """
        🛠 Create an E2E instance.

        Args:
            name (str): The name of the instance.
            image (str): The image ID or name.
            plan (str): The plan ID.
            ssh_keys (Optional[list]): The list of SSH keys for the instance.
            open_ports (Optional[list]): The list of ports to open for the instance.
            tags (Optional[list]): The list of tags for the instance.
            region (str): The region for the instance. Defaults to "ncr".
            backup (bool): Enable backups for the instance. Defaults to False.
            **kwargs: Additional keyword arguments for instance creation.
        """
        security_group_id = self.create_security_group(f"{name}-sg", open_ports or [])
        url = f"{self.base_url}/nodes/?apikey={self.api_key}&project_id={self.project_id}"
        payload = {
            "name": name,
            "region": region,
            "plan": plan,
            "image": image,
            "ssh_keys": ssh_keys or [],
            "backups": backup,
            "security_group_id": security_group_id,
            "tags": tags or [],
        }
        payload.update(kwargs)
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        self.log.info(f"🚀 Created instance {name}")
        print_json(response.json())

    def get_node(self, node_id: str):
        """
        📝 Get details of an E2E instance.

        Args:
            node_id (str): The ID of the instance.
        """
        url = f"{self.base_url}/nodes/{node_id}/?apikey={self.api_key}&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        self.log.info(f"ℹ️ Instance details for {node_id}:")
        print_json(response.json())

    def list_nodes(self):
        """
        📋 List E2E instances.
        """
        url = f"{self.base_url}/nodes/?apikey={self.api_key}&page_no=1&per_page=2&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        self.log.info("📋 List of instances:")
        print_json(response.json())

    def delete_node(self, node_id: str):
        """
        🗑️ Delete an E2E instance.

        Args:
            node_id (str): The ID of the instance to delete.
        """
        url = f"{self.base_url}/nodes/{node_id}/?reserve_ip_required=&reserve_ip_pool_required=&apikey={self.api_key}&project_id={self.project_id}&location={self.location}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        self.log.info(f"🗑️ Deleted instance {node_id}")
        print_json(response.json())
