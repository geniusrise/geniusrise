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

from geniusrise.runners.openstack.autoscale import OpenStackAutoscaleRunner
from argparse import ArgumentParser, Namespace


class AceCloudAutoscaleRunner(OpenStackAutoscaleRunner):
    r"""
    🚀 Initialize the AceCloudAutoscaleRunner class for managing autoscaled deployments with a load balancer.

    CLI Usage:
        genius acecloud-autoscale [sub-command] [options]
        Examples:

        ```bash
        genius acecloud-autoscale create --name example-autoscale --image ubuntu --flavor m1.small --key-name mykey --network my-network \
            --min-instances 2 --max-instances 5 --desired-instances 3 --protocol HTTPS \
            --scale-up-threshold 80 --scale-up-adjustment 1 --scale-down-threshold 20 --scale-down-adjustment -1 \
            --alarm-period 60 --alarm-evaluation-periods 1 --user-data "#!/bin/bash\napt-get update\napt-get install -y apache2" \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius acecloud-autoscale delete --name example-autoscale \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius acecloud-autoscale status --name example-autoscale \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

    YAML Configuration:

    ```yaml
    version: "1.0"
    autoscale:
        - name: "example-autoscale"
        image: "ubuntu"
        flavor: "m1.small"
        key_name: "mykey"
        network: "my-network"
        min_instances: 2
        max_instances: 5
        desired_instances: 3
        protocol: "HTTPS"
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
        auth_url: "https://openstack.example.com:5000/v3"
        username: "myuser"
        password: "mypassword"
        project_name: "myproject"
    ```
    """

    auth_url = ""

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🛠 Add common connection arguments to a parser.

        Args:
            parser (ArgumentParser): The parser to which arguments will be added.

        Returns:
            ArgumentParser: The parser with added arguments.
        """
        # fmt: off
        parser.add_argument("--username", help="OpenStack username.", type=str, required=True)
        parser.add_argument("--password", help="OpenStack password.", type=str, required=True)
        parser.add_argument("--project-name", help="OpenStack project name.", type=str, required=True)
        # fmt: on
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to OpenStack autoscale functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="acecloud")

        # Parser for create
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
        create_parser.add_argument("--scale-up-threshold", help="Threshold for triggering scale-up action.", type=int, default=80)
        create_parser.add_argument("--scale-up-adjustment", help="Number of instances to add during scale-up.", type=int, default=1)
        create_parser.add_argument("--scale-down-threshold", help="Threshold for triggering scale-down action.", type=int, default=20)
        create_parser.add_argument("--scale-down-adjustment", help="Number of instances to remove during scale-down.", type=int, default=-1)
        create_parser.add_argument("--alarm-period", help="Period for alarms (in seconds).", type=int, default=60)
        create_parser.add_argument("--alarm-evaluation-periods", help="Number of periods to evaluate alarms.", type=int, default=1)
        create_parser.add_argument("--user-data", help="User data script for instances.", type=str, default="#!/bin/bash\napt-get update")
        create_parser = self._add_connection_args(create_parser)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete an autoscaled deployment.")
        delete_parser.add_argument("name", help="Name of the autoscaled deployment.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Show the status of an autoscaled deployment.")
        status_parser.add_argument("name", help="Name of the autoscaled deployment.", type=str)
        status_parser = self._add_connection_args(status_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the OpenStack autoscale manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """
        self.connect(
            auth_url=self.auth_url,
            username=args.username,
            password=args.password,
            project_name=args.project_name,
        )

        if args.acecloud == "create":
            self.create(
                name=args.name,
                image=args.image,
                flavor=args.flavor,
                key_name=args.key_name,
                network=args.network,
                min_instances=args.min_instances,
                max_instances=args.max_instances,
                desired_instances=args.desired_instances,
                protocol=args.protocol,
                scale_up_threshold=args.scale_up_threshold,
                scale_up_adjustment=args.scale_up_adjustment,
                scale_down_threshold=args.scale_down_threshold,
                scale_down_adjustment=args.scale_down_adjustment,
                alarm_period=args.alarm_period,
                alarm_evaluation_periods=args.alarm_evaluation_periods,
                user_data=args.user_data,
            )
        elif args.acecloud == "delete":
            self.delete(name=args.name)
        elif args.acecloud == "status":
            self.status(name=args.name)
        else:
            raise ValueError(f"Unknown command: {args.acecloud}")
