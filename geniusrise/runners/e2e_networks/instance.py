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
from argparse import ArgumentParser, Namespace
from typing import Optional, List


class E2EInstanceRunner:
    def __init__(self):
        self.api_key: str = ""
        self.project_id: str = ""
        self.location: str = ""
        self.base_url: str = "https://api.e2enetworks.com/myaccount/api/v1"
        self.headers: dict = {}

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--api-key", help="API key for E2E Networks.", type=str, required=True)
        parser.add_argument("--project-id", help="Project ID for E2E Networks.", type=str, required=True)
        parser.add_argument("--location", help="Location for E2E Networks.", type=str, required=True)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="e2e_instance")

        create_parser = subparsers.add_parser("create", help="Create a new instance.")
        create_parser.add_argument("name", help="Name of the instance.", type=str)
        create_parser.add_argument("image", help="Image ID or name.", type=str)
        create_parser.add_argument("flavor", help="Flavor ID or name.", type=str)
        create_parser.add_argument("--ssh-keys", help="SSH keys for the instance.", type=str, nargs="+")
        create_parser.add_argument("--open-ports", help="Ports to be opened for the instance.", type=str, nargs="+")
        create_parser.add_argument("--tags", help="Tags for the instance.", type=str, nargs="+")
        create_parser.add_argument("--region", help="Region for the instance.", type=str, default="ncr")
        create_parser = self._add_connection_args(create_parser)

        get_parser = subparsers.add_parser("get", help="Get details of an instance.")
        get_parser.add_argument("node_id", help="ID of the instance.", type=str)
        get_parser = self._add_connection_args(get_parser)

        list_parser = subparsers.add_parser("list", help="List instances.")
        list_parser = self._add_connection_args(list_parser)

        delete_parser = subparsers.add_parser("delete", help="Delete an instance.")
        delete_parser.add_argument("node_id", help="ID of the instance.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        return parser

    def run(self, args: Namespace) -> None:
        self.api_key = args.api_key
        self.project_id = args.project_id
        self.location = args.location
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        if args.e2e_instance == "create":
            self.create_node(args.name, args.image, args.flavor, args.ssh_keys, args.open_ports, args.tags, args.region)
        elif args.e2e_instance == "get":
            self.get_node(args.node_id)
        elif args.e2e_instance == "list":
            self.list_nodes()
        elif args.e2e_instance == "delete":
            self.delete_node(args.node_id)
        else:
            raise ValueError(f"Unknown command: {args.e2e_instance}")

    def create_security_group(self, name: str, open_ports: List[str]) -> int:
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
        return data["data"]["resource_type"]

    def create_node(
        self,
        name: str,
        image: str,
        flavor: str,
        ssh_keys: Optional[List[str]] = None,
        open_ports: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        region: str = "ncr",
        **kwargs,
    ):
        security_group_id = self.create_security_group(f"{name}-sg", open_ports or [])
        url = f"{self.base_url}/nodes/?apikey={self.api_key}&project_id={self.project_id}"
        payload = {
            "name": name,
            "region": region,
            "plan": flavor,
            "image": image,
            "ssh_keys": ssh_keys or [],
            "backups": False,
            "security_group_id": security_group_id,
            "tags": tags or [],
        }
        payload.update(kwargs)
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        print(response.json())

    def get_node(self, node_id: str):
        url = f"{self.base_url}/nodes/{node_id}/?apikey={self.api_key}&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        print(response.json())

    def list_nodes(self):
        url = f"{self.base_url}/nodes/?apikey={self.api_key}&page_no=1&per_page=2&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        print(response.json())

    def delete_node(self, node_id: str):
        url = f"{self.base_url}/nodes/{node_id}/?reserve_ip_required=&reserve_ip_pool_required=&apikey={self.api_key}&project_id={self.project_id}&location={self.location}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        print(response.json())
