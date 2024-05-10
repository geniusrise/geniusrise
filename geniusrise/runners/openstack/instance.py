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

from argparse import ArgumentParser, Namespace
from typing import Optional, Any

from openstack import connection  # type: ignore


class OpenStackInstanceRunner:
    r"""
    🚀 Initialize the OpenStackInstanceRunner class for managing OpenStack EC2 instances.

    CLI Usage:
        genius openstack [sub-command] [options]
        Examples:

        ```bash
        genius openstack create --name example-instance --image ubuntu --flavor m1.small --key-name mykey --network my-network \
            --block-storage-size 10 --open-ports 80,443 --user-data "#!/bin/bash\napt-get update\napt-get install -y apache2" \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius openstack delete --name example-instance \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius openstack show --name example-instance \
            --auth-url https://openstack.example.com:5000/v3 --username myuser --password mypassword --project-name myproject
        ```

    YAML Configuration:

    ```yaml
    version: "1.0"
    instances:
        - name: "example-instance"
        image: "ubuntu"
        flavor: "m1.small"
        key_name: "mykey"
        network: "my-network"
        block_storage_size: 10
        open_ports:
            - 80
            - 443
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
        🚀 Initialize the OpenStackInstanceRunner class for managing OpenStack EC2 instances.
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
        🎛 Create a parser for CLI commands related to OpenStack EC2 functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="openstack")

        # Parser for create
        # fmt: off
        create_parser = subparsers.add_parser("create", help="Create a new instance.")
        create_parser.add_argument("name", help="Name of the instance.", type=str)
        create_parser.add_argument("image", help="Image ID or name.", type=str)
        create_parser.add_argument("flavor", help="Flavor ID or name.", type=str)
        create_parser.add_argument("--key-name", help="Key pair name.", type=str)
        create_parser.add_argument("--allocate-ip", help="Allocate an IP address. Requires network to be public.", type=bool, default=False)
        create_parser.add_argument("--network", help="Network ID or name.", type=str)
        create_parser.add_argument("--block-storage-size", help="Size of the block storage in GB.", type=int)
        create_parser.add_argument("--open-ports", help="Comma-separated list of ports to open.", type=str)
        create_parser.add_argument("--user-data", help="User data script for instances.", type=str, default="#!/bin/bash")
        create_parser = self._add_connection_args(create_parser)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete an instance.")
        delete_parser.add_argument("name", help="Name of the instance.", type=str)
        delete_parser = self._add_connection_args(delete_parser)

        # Parser for show
        show_parser = subparsers.add_parser("show", help="Show details of an instance.")
        show_parser.add_argument("name", help="Name of the instance.", type=str)
        show_parser = self._add_connection_args(show_parser)

        # fmt: on
        return parser

    def run(self, args: Namespace) -> None:
        """
        🚀 Run the OpenStack EC2 manager.

        Args:
            args (Namespace): The parsed command line arguments.
        """
        self.connect(
            auth_url=args.auth_url,
            username=args.username,
            password=args.password,
            project_name=args.project_name,
        )

        if args.openstack == "create":
            self.create(
                name=args.name,
                image=args.image,
                flavor=args.flavor,
                key_name=args.key_name,
                allocate_ip=args.allocate_ip,
                network=args.network,
                block_storage_size=args.block_storage_size,
                open_ports=args.open_ports,
                user_data=args.user_data,
            )
        elif args.openstack == "delete":
            self.delete(name=args.name)
        elif args.openstack == "show":
            self.status(name=args.name)
        else:
            raise ValueError(f"Unknown command: {args.openstack}")

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
        allocate_ip: bool = False,
        network: Optional[str] = None,
        block_storage_size: Optional[int] = None,
        open_ports: Optional[str] = None,
        user_data: str = "#!/bin/bash",
    ) -> Any:
        """
        🛠 Create an OpenStack EC2 instance.

        Args:
            name (str): Name of the instance.
            image (str): Image ID or name.
            flavor (str): Flavor ID or name.
            key_name (Optional[str]): Key pair name.
            allocate_ip (bool): Whether a floating IP should be allocated. Also requires the network param.
            network (Optional[str]): Network ID or name.
            block_storage_size (Optional[int]): Size of the block storage in GB.
            open_ports (Optional[str]): Comma-separated list of ports to open.
            user_data (str): User data script for instances.
        """
        image = self.conn.compute.find_image(image)
        flavor = self.conn.compute.find_flavor(flavor)

        if network:
            network = self.conn.network.find_network(network)
            nics = [{"net-id": network.id}]  # type: ignore
        else:
            nics = None

        # Create security group and open specified ports
        if open_ports:
            security_group = self.conn.network.create_security_group(
                name=f"{name}-security-group",
                description=f"Security group for {name} instance",
            )
            for port in open_ports.split(","):
                self.conn.network.create_security_group_rule(
                    security_group_id=security_group.id,
                    direction="ingress",
                    ethertype="IPv4",
                    port_range_min=int(port),
                    port_range_max=int(port),
                    protocol="tcp",
                )
        else:
            security_group = None

        instance = self.conn.compute.create_server(
            name=name,
            image_id=image.id,  # type: ignore
            flavor_id=flavor.id,  # type: ignore
            key_name=key_name,
            nics=nics,
            security_groups=[security_group.name] if security_group else None,  # type: ignore
            user_data=user_data,
        )

        # Attach block storage if specified
        if block_storage_size:
            volume = self.conn.block_storage.create_volume(
                name=f"{name}-volume",
                size=block_storage_size,
            )
            self.conn.compute.create_volume_attachment(
                server=instance,
                volumeId=volume.id,
            )
            print(f"🗃️ Attached block storage of size {block_storage_size}GB to instance {name}")

        # Allocate a floating IP address
        if allocate_ip and network:
            floating_ip = self.conn.network.create_ip(floating_network_id=network.id)  # type: ignore
            self.conn.compute.add_floating_ip_to_server(instance, floating_ip.floating_ip_address)
            print(f"🌐 Allocated floating IP address {floating_ip.floating_ip_address} to instance {name}")

        print(f"🛠️ Created instance {name} with ID {instance.id}")
        return instance

    def delete(self, name: str) -> None:
        """
        🗑 Delete an OpenStack EC2 instance.

        Args:
            name (str): Name of the instance.
        """
        instance = self.conn.compute.find_server(name)
        self.conn.compute.delete_server(instance.id)
        print(f"🗑️ Deleted instance {name}")

    def status(self, name: str) -> Any:
        """
        📊 Show details of an OpenStack EC2 instance.

        Args:
            name (str): Name of the instance.
        """
        instance = self.conn.compute.find_server(name)
        print(f"📊 Instance {name} details:")
        print(f"  ID: {instance.id}")
        print(f"  Status: {instance.status}")
        print(f"  Image: {instance.image['id']}")
        print(f"  Flavor: {instance.flavor['id']}")
        print(f"  Key Name: {instance.key_name}")
        print(f"  Networks: {instance.addresses}")
        return instance
