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

from argparse import ArgumentParser, Namespace
from typing import Optional, Any

from openstack import connection  # type: ignore


class OpenStackAutoscaleRunner:
    r"""
    🚀 Initialize the OpenStackAutoscaleRunner class for managing autoscaled deployments with a load balancer.

    CLI Usage:
        genius openstack-autoscale [sub-command] [options]
        Examples:

        ```bash
        genius openstack-autoscale create --name example-autoscale --image ubuntu --flavor m1.small --key-name mykey --network my-network \
            --min-instances 2 --max-instances 5 --desired-instances 3 --protocol HTTPS \
            --scale-up-threshold 80 --scale-up-adjustment 1 --scale-down-threshold 20 --scale-down-adjustment -1 \
            --alarm-period 60 --alarm-evaluation-periods 1 --user-data "#!/bin/bash\napt-get update\napt-get install -y apache2" \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius openstack-autoscale delete --name example-autoscale \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius openstack-autoscale status --name example-autoscale \
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

    def __init__(self):
        """
        🚀 Initialize the OpenStackAutoscaleRunner class for managing autoscaled deployments with a load balancer.
        """
        self.conn: connection.Connection = None  # type: ignore

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🛠 Add common connection arguments to a parser.

        Args:
            parser (ArgumentParser): The parser to which arguments will be added.

        Returns:
            ArgumentParser: The parser with added arguments.
        """
        # fmt: off
        parser.add_argument("--auth-url", help="Authentication URL.", type=str, required=True)
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
        subparsers = parser.add_subparsers(dest="openstack-autoscale")

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
            auth_url=args.auth_url,
            username=args.username,
            password=args.password,
            project_name=args.project_name,
        )

        if args.openstack_autoscale == "create":
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
        elif args.openstack_autoscale == "delete":
            self.delete(name=args.name)
        elif args.openstack_autoscale == "status":
            self.status(name=args.name)
        else:
            raise ValueError(f"Unknown command: {args.openstack_autoscale}")

    def connect(self, auth_url: str, username: str, password: str, project_name: str) -> None:
        """
        🌐 Connect to OpenStack.

        Args:
            auth_url (str): Authentication URL.
            username (str): OpenStack username.
            password (str): OpenStack password.
            project_name (str): OpenStack project name.
        """
        self.conn = connection.Connection(
            auth_url=auth_url,
            username=username,
            password=password,
            project_name=project_name,
        )

    def create(
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
        scale_up_threshold: int = 80,
        scale_up_adjustment: int = 1,
        scale_down_threshold: int = 20,
        scale_down_adjustment: int = -1,
        alarm_period: int = 60,
        alarm_evaluation_periods: int = 5,
        user_data: str = "#!/bin/bash\napt-get update",
    ) -> Any:
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
            scale_up_threshold (int): Threshold for triggering scale-up action.
            scale_up_adjustment (int): Number of instances to add during scale-up.
            scale_down_threshold (int): Threshold for triggering scale-down action.
            scale_down_adjustment (int): Number of instances to remove during scale-down.
            alarm_period (int): Period for alarms (in seconds).
            alarm_evaluation_periods (int): Number of periods to evaluate alarms.
            user_data (str): User data script for instances.
        """
        # Create a stack for autoscaling
        stack = self.conn.orchestration.create_stack(
            name=f"{name}-stack",
            template={
                "heat_template_version": "2016-10-14",
                "resources": {
                    "loadbalancer": {
                        "type": "OS::Octavia::LoadBalancer",
                        "properties": {
                            "name": f"{name}-lb",
                            "vip_subnet": self.conn.network.find_network(network).subnets[0].id if network else None,
                        },
                    },
                    "listener": {
                        "type": "OS::Octavia::Listener",
                        "properties": {
                            "name": f"{name}-listener",
                            "protocol": protocol,
                            "protocol_port": 443 if protocol == "HTTPS" else 80,
                            "loadbalancer": {"get_resource": "loadbalancer"},
                        },
                    },
                    "pool": {
                        "type": "OS::Octavia::Pool",
                        "properties": {
                            "name": f"{name}-pool",
                            "lb_algorithm": "ROUND_ROBIN",
                            "protocol": protocol,
                            "listener": {"get_resource": "listener"},
                        },
                    },
                    "healthmonitor": {
                        "type": "OS::Octavia::HealthMonitor",
                        "properties": {
                            "pool": {"get_resource": "pool"},
                            "type": protocol,
                            "delay": 5,
                            "timeout": 2,
                            "max_retries": 3,
                        },
                    },
                    "autoscaling_group": {
                        "type": "OS::Heat::AutoScalingGroup",
                        "properties": {
                            "min_size": min_instances,
                            "max_size": max_instances,
                            "desired_capacity": desired_instances,
                            "resource": {
                                "type": "OS::Nova::Server",
                                "properties": {
                                    "name": f"{name}-instance",
                                    "image": self.conn.compute.find_image(image).id,
                                    "flavor": self.conn.compute.find_flavor(flavor).id,
                                    "key_name": key_name,
                                    "user_data": user_data,
                                },
                            },
                            "pool_id": {"get_resource": "pool"},
                        },
                    },
                    "scale_up_policy": {
                        "type": "OS::Heat::ScalingPolicy",
                        "properties": {
                            "adjustment_type": "change_in_capacity",
                            "auto_scaling_group_id": {"get_resource": "autoscaling_group"},
                            "cooldown": 60,
                            "scaling_adjustment": scale_up_adjustment,
                        },
                    },
                    "scale_up_alarm": {
                        "type": "OS::Ceilometer::Alarm",
                        "properties": {
                            "meter_name": "cpu_util",
                            "statistic": "avg",
                            "period": alarm_period,
                            "evaluation_periods": alarm_evaluation_periods,
                            "threshold": scale_up_threshold,
                            "alarm_actions": [{"get_attr": ["scale_up_policy", "alarm_url"]}],
                            "matching_metadata": {"metadata.user_metadata.stack": {"get_param": "OS::stack_id"}},
                            "comparison_operator": "gt",
                        },
                    },
                    "scale_down_policy": {
                        "type": "OS::Heat::ScalingPolicy",
                        "properties": {
                            "adjustment_type": "change_in_capacity",
                            "auto_scaling_group_id": {"get_resource": "autoscaling_group"},
                            "cooldown": 60,
                            "scaling_adjustment": scale_down_adjustment,
                        },
                    },
                    "scale_down_alarm": {
                        "type": "OS::Ceilometer::Alarm",
                        "properties": {
                            "meter_name": "cpu_util",
                            "statistic": "avg",
                            "period": alarm_period,
                            "evaluation_periods": alarm_evaluation_periods,
                            "threshold": scale_down_threshold,
                            "alarm_actions": [{"get_attr": ["scale_down_policy", "alarm_url"]}],
                            "matching_metadata": {"metadata.user_metadata.stack": {"get_param": "OS::stack_id"}},
                            "comparison_operator": "lt",
                        },
                    },
                },
            },
        )
        print(f"🚀 Created autoscaled deployment {name}")
        print(f"🌐 Load Balancer: {stack.outputs[0]['output_value']}")

    def delete(self, name: str) -> None:
        """
        🗑 Delete an autoscaled deployment.

        Args:
            name (str): Name of the autoscaled deployment.
        """
        # Delete the autoscaling stack
        stack = self.conn.orchestration.find_stack(f"{name}-stack")
        self.conn.orchestration.delete_stack(stack)

        print(f"🗑️ Deleted autoscaled deployment {name}")

    def status(self, name: str) -> Any:
        """
        📊 Show the status of an autoscaled deployment.

        Args:
            name (str): Name of the autoscaled deployment.
        """
        # Get the autoscaling stack
        stack = self.conn.orchestration.find_stack(f"{name}-stack")

        print(f"📊 Autoscaled Deployment {name} Status:")
        print(f"  ID: {stack.id}")
        print(f"  Status: {stack.status}")
        print(f"  Status Reason: {stack.status_reason}")

        # Get the autoscaling group
        autoscaling_group = self.conn.orchestration.resources(stack_id=stack.id, nested_depth=2).find(
            resource_type="OS::Heat::AutoScalingGroup"
        )

        print(f"  Autoscaling Group: {autoscaling_group.physical_resource_id}")
        print(f"    Min Instances: {autoscaling_group.attributes['min_size']}")
        print(f"    Max Instances: {autoscaling_group.attributes['max_size']}")
        print(f"    Desired Instances: {autoscaling_group.attributes['desired_capacity']}")
        print(f"    Current Instances: {autoscaling_group.attributes['current_size']}")

        return stack
