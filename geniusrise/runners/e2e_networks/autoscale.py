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


class E2EAutoscaleRunner:
    r"""
    🚀 Initialize the E2EAutoscaleRunner class for managing autoscaled deployments with a load balancer.

    CLI Usage:
        genius e2e-autoscale [sub-command] [options]
        Examples:

        ```bash
        genius e2e-autoscale create --name example-autoscale --image Ubuntu-20.04 --flavor C1.1GB --key-name mykey --network my-network \
            --min-instances 2 --max-instances 5 --desired-instances 3 --protocol HTTPS --port 443 --target-port 8080 \
            --scale-up-threshold 80 --scale-up-adjustment 1 --scale-down-threshold 20 --scale-down-adjustment -1 \
            --alarm-period 60 --alarm-evaluation-periods 1 --user-data "#!/bin/bash\napt-get update\napt-get install -y apache2" \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

        ```bash
        genius e2e-autoscale delete --name example-autoscale \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

        ```bash
        genius e2e-autoscale status --name example-autoscale \
            --api-key <api-key> --project-id <project-id> --location Delhi
        ```

    YAML Configuration:

    ```yaml
    version: "1.0"
    autoscale:
        - name: "example-autoscale"
        image: "Ubuntu-20.04"
        flavor: "C1.1GB"
        key_name: "mykey"
        network: "my-network"
        min_instances: 2
        max_instances: 5
        desired_instances: 3
        protocol: "HTTPS"
        port: 443
        target_port: 8080
        scale_up_threshold: 80
        scale_up_adjustment: 1
        scale_down_threshold: 20
        scale_down_adjustment: -1
        alarm_period: 60
        alarm_evaluation_periods: 1
        user_data: |
            #!/bin/bash
            apt-get update
            apt-get install -y apache2
        api_key: "<api-key>"
        project_id: "<project-id>"
        location: "Delhi"
    ```
    """

    def __init__(self):
        """
        🚀 Initialize the E2EAutoscaleRunner class for managing autoscaled deployments with a load balancer.
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
        🎛 Create a parser for CLI commands related to E2E autoscale functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="e2e_autoscale")

        # fmt: off
        create_parser = subparsers.add_parser("create", help="Create a new autoscaled deployment.")
        create_parser.add_argument("name", help="Name of the autoscaled deployment.", type=str)
        create_parser.add_argument("image", help="Image ID or name.", type=str)
        create_parser.add_argument("flavor", help="Flavor ID or name.", type=str)
        create_parser.add_argument("--key-name", help="Key pair name.", type=str)
        create_parser.add_argument("--network", help="Network ID or name.", type=str)
        create_parser.add_argument("--min-instances", help="Minimum number of instances.", type=int, default=1)
        create_parser.add_argument("--max-instances", help="Maximum number of instances.", type=int, default=5)
        create_parser.add_argument("--desired-instances", help="Desired number of instances.", type=int, default=2)
        create_parser.add_argument("--protocol", help="Load balancer protocol (HTTP or HTTPS).", type=str, default="HTTP")
        create_parser.add_argument("--port", help="Load balancer port.", type=int, default=80)
        create_parser.add_argument("--target-port", help="Backend target port.", type=int, default=80)
        create_parser.add_argument("--scale-up-threshold", help="Threshold for triggering scale-up action.", type=int, default=80)
        create_parser.add_argument("--scale-up-adjustment", help="Number of instances to add during scale-up.", type=int, default=1)
        create_parser.add_argument("--scale-down-threshold", help="Threshold for triggering scale-down action.", type=int, default=20)
        create_parser.add_argument("--scale-down-adjustment", help="Number of instances to remove during scale-down.", type=int, default=-1)
        create_parser.add_argument("--alarm-period", help="Period for alarms (in seconds).", type=int, default=60)
        create_parser.add_argument("--alarm-evaluation-periods", help="Number of periods to evaluate alarms.", type=int, default=1)
        create_parser.add_argument("--user-data", help="User data script for instances.", type=str, default="")
        create_parser = self._add_connection_args(create_parser)

        delete_parser = subparsers.add_parser("delete", help="Delete an autoscaled deployment.")
        delete_parser.add_argument("name", help="Name of the autoscaled deployment.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        status_parser = subparsers.add_parser("status", help="Show the status of an autoscaled deployment.")
        status_parser.add_argument("name", help="Name of the autoscaled deployment.", type=str)
        status_parser = self._add_connection_args(status_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the E2E autoscale manager.

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

        if args.e2e_autoscale == "create":
            self.create_autoscale(
                args.name,
                args.image,
                args.flavor,
                args.key_name,
                args.network,
                args.min_instances,
                args.max_instances,
                args.desired_instances,
                args.protocol,
                args.port,
                args.target_port,
                args.scale_up_threshold,
                args.scale_up_adjustment,
                args.scale_down_threshold,
                args.scale_down_adjustment,
                args.alarm_period,
                args.alarm_evaluation_periods,
                args.user_data,
            )
        elif args.e2e_autoscale == "delete":
            self.delete_autoscale(args.name)
        elif args.e2e_autoscale == "status":
            self.autoscale_status(args.name)
        else:
            raise ValueError(f"Unknown command: {args.e2e_autoscale}")

    def create_autoscale(
        self,
        name: str,
        image: str,
        flavor: str,
        key_name: Optional[str] = None,
        network: Optional[str] = None,
        min_instances: int = 1,
        max_instances: int = 5,
        desired_instances: int = 2,
        protocol: str = "HTTP",
        port: int = 80,
        target_port: int = 80,
        scale_up_threshold: int = 80,
        scale_up_adjustment: int = 1,
        scale_down_threshold: int = 20,
        scale_down_adjustment: int = -1,
        alarm_period: int = 60,
        alarm_evaluation_periods: int = 1,
        user_data: str = "",
    ):
        """
        🛠 Create an autoscaled deployment with a load balancer.

        Args:
            name (str): Name of the autoscaled deployment.
            image (str): Image ID or name.
            flavor (str): Flavor ID or name.
            key_name (Optional[str]): Key pair name.
            network (Optional[str]): Network ID or name.
            min_instances (int): Minimum number of instances.
            max_instances (int): Maximum number of instances.
            desired_instances (int): Desired number of instances.
            protocol (str): Load balancer protocol (HTTP or HTTPS).
            port (int): Load balancer port.
            target_port (int): Backend target port.
            scale_up_threshold (int): Threshold for triggering scale-up action.
            scale_up_adjustment (int): Number of instances to add during scale-up.
            scale_down_threshold (int): Threshold for triggering scale-down action.
            scale_down_adjustment (int): Number of instances to remove during scale-down.
            alarm_period (int): Period for alarms (in seconds).
            alarm_evaluation_periods (int): Number of periods to evaluate alarms.
            user_data (str): User data script for instances.
        """
        url = f"{self.base_url}/scaler/scalegroups/?apikey={self.api_key}&project_id={self.project_id}"
        payload = {
            "name": name,
            "min_nodes": min_instances,
            "desired": desired_instances,
            "max_nodes": max_instances,
            "plan_id": self.get_flavor_id(flavor),
            "plan_name": flavor,
            "sku_id": self.get_flavor_id(flavor),
            "policy": [
                {
                    "type": "CHANGE",
                    "adjust": scale_up_adjustment,
                    "expression": f"CPU>{scale_up_threshold}",
                    "period_number": alarm_evaluation_periods,
                    "period": alarm_period,
                    "cooldown": "150",
                },
                {
                    "type": "CHANGE",
                    "adjust": scale_down_adjustment,
                    "expression": f"CPU<{scale_down_threshold}",
                    "period_number": alarm_evaluation_periods,
                    "period": alarm_period,
                    "cooldown": "150",
                },
            ],
            "vm_image_id": self.get_image_id(image),
            "vm_image_name": image,
            "vm_template_id": self.get_template_id(image),
            "my_account_sg_id": self.create_security_group(f"{name}-sg", [str(port), str(target_port)]),
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        self.log.info(f"🚀 Created autoscaled deployment {name}")
        print_json(data)

        # Create the load balancer
        lb_url = f"{self.base_url}/appliances/load-balancers/?apikey={self.api_key}&project_id={self.project_id}"
        lb_payload = {
            "name": f"{name}-lb",
            "plan_name": "E2E-LB-1",
            "lb_name": f"{name}-lb",
            "lb_type": "External",
            "lb_mode": protocol,
            "lb_port": port,
            "node_list_type": "S",
            "checkbox_enable": "",
            "lb_reserve_ip": "",
            "ssl_certificate_id": "",
            "ssl_context": {"redirect_to_https": False},
            "enable_bitninja": False,
            "backends": [
                {
                    "balance": "roundrobin",
                    "checkbox_enable": False,
                    "domain_name": "localhost",
                    "check_url": "/",
                    "servers": [
                        {
                            "backend_name": name,
                            "backend_ip": data["data"]["nodes"][0]["private_ip"],
                            "backend_port": target_port,
                        }
                    ],
                    "http_check": False,
                }
            ],
            "acl_list": [],
            "acl_map": [],
            "vpc_list": [],
            "scaler_id": data["data"]["id"],
            "scaler_port": target_port,
            "tcp_backend": [],
        }
        lb_response = requests.post(lb_url, headers=self.headers, json=lb_payload)
        lb_response.raise_for_status()
        lb_data = lb_response.json()
        self.log.info(f"🌐 Created load balancer {name}-lb")
        print_json(lb_data)

    def delete_autoscale(self, name: str):
        """
        🗑️ Delete an autoscaled deployment.

        Args:
            name (str): Name of the autoscaled deployment.
        """
        # Get the autoscaled deployment ID
        url = f"{self.base_url}/scaler/scalegroups?apikey={self.api_key}&project_id={self.project_id}&location={self.location}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        autoscale_id = next((item["id"] for item in data["data"] if item["name"] == name), None)

        if autoscale_id:
            # Delete the autoscaled deployment
            delete_url = (
                f"{self.base_url}/scaler/scalegroups/{autoscale_id}/?apikey={self.api_key}&project_id={self.project_id}"
            )
            delete_response = requests.delete(delete_url, headers=self.headers)
            delete_response.raise_for_status()
            self.log.info(f"🗑️ Deleted autoscaled deployment {name}")
        else:
            self.log.warning(f"⚠️ Autoscaled deployment {name} not found")

        # Delete the load balancer
        lb_url = (
            f"{self.base_url}/appliances/?location={self.location}&apikey={self.api_key}&project_id={self.project_id}"
        )
        lb_response = requests.get(lb_url, headers=self.headers)
        lb_response.raise_for_status()
        lb_data = lb_response.json()
        lb_id = next((item["id"] for item in lb_data["data"] if item["name"] == f"{name}-lb"), None)

        if lb_id:
            delete_lb_url = f"{self.base_url}/appliances/{lb_id}/?apikey={self.api_key}&project_id={self.project_id}"
            delete_lb_response = requests.delete(delete_lb_url, headers=self.headers)
            delete_lb_response.raise_for_status()
            self.log.info(f"🗑️ Deleted load balancer {name}-lb")
        else:
            self.log.warning(f"⚠️ Load balancer {name}-lb not found")

    def autoscale_status(self, name: str):
        """
        📊 Show the status of an autoscaled deployment.

        Args:
            name (str): Name of the autoscaled deployment.
        """
        # Get the autoscaled deployment
        url = f"{self.base_url}/scaler/scalegroups?apikey={self.api_key}&project_id={self.project_id}&location={self.location}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        autoscale = next((item for item in data["data"] if item["name"] == name), None)

        if autoscale:
            print(f"📊 Autoscaled Deployment {name} Status:")
            print(f"  ID: {autoscale['id']}")
            print(f"  Status: {autoscale['provision_status']}")
            print(f"  Min Instances: {autoscale['min_nodes']}")
            print(f"  Max Instances: {autoscale['max_nodes']}")
            print(f"  Desired Instances: {autoscale['desired']}")
            print(f"  Current Instances: {len(autoscale['nodes'])}")
            print(f"  Policy: {autoscale['policy']}")
        else:
            self.log.warning(f"⚠️ Autoscaled deployment {name} not found")

    def get_flavor_id(self, flavor_name: str) -> int:
        """
        🍨 Get the ID of a flavor by its name.

        Args:
            flavor_name (str): Name of the flavor.

        Returns:
            int: ID of the flavor.
        """
        url = f"{self.base_url}/sizes/?apikey={self.api_key}&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        flavor = next((item for item in data["data"] if item["name"] == flavor_name), None)
        if flavor:
            return flavor["id"]
        else:
            raise ValueError(f"Flavor {flavor_name} not found")

    def get_image_id(self, image_name: str) -> int:
        """
        🖼️ Get the ID of an image by its name.

        Args:
            image_name (str): Name of the image.

        Returns:
            int: ID of the image.
        """
        url = f"{self.base_url}/images/?apikey={self.api_key}&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        image = next((item for item in data["data"] if item["name"] == image_name), None)
        if image:
            return image["id"]
        else:
            raise ValueError(f"Image {image_name} not found")

    def get_template_id(self, image_name: str) -> int:
        """
        📜 Get the template ID of an image by its name.

        Args:
            image_name (str): Name of the image.

        Returns:
            int: Template ID of the image.
        """
        url = f"{self.base_url}/images/?apikey={self.api_key}&project_id={self.project_id}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        data = response.json()
        image = next((item for item in data["data"] if item["name"] == image_name), None)
        if image:
            return image["template_id"]
        else:
            raise ValueError(f"Image {image_name} not found")

    def create_security_group(self, name: str, ports: list) -> int:
        """
        🛡️ Create a security group.

        Args:
            name (str): Name of the security group.
            ports (list): List of ports to open.

        Returns:
            int: ID of the created security group.
        """
        url = f"{self.base_url}/security_group/?apikey={self.api_key}&project_id={self.project_id}&location={self.location}"
        payload = {
            "name": name,
            "description": f"Security group for {name}",
            "rules": [
                {
                    "network": "any",
                    "rule_type": "Inbound",
                    "protocol_name": "Custom_TCP",
                    "port_range": ",".join(ports),
                },
                {
                    "network": "any",
                    "rule_type": "Outbound",
                    "protocol_name": "All",
                    "port_range": "All",
                },
            ],
            "default": False,
        }
        response = requests.post(url, headers=self.headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["data"]["id"]
