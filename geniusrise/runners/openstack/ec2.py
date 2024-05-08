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


class OpenStackNovaRunner:
    r"""
    🚀 Initialize the OpenStackNovaRunner class for managing OpenStack EC2 instances.

    CLI Usage:
        genius openstack [sub-command] [options]
        Examples:

        ```bash
        genius openstack create --name example-instance --image ubuntu --flavor m1.small --key-name mykey --network my-network \
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
        auth_url: "https://openstack.example.com:5000/v3"
        username: "myuser"
        password: "mypassword"
        project_name: "myproject"
    ```
    """

    def __init__(self):
        """
        🚀 Initialize the OpenStackNovaRunner class for managing OpenStack EC2 instances.
        """
        self.conn: connection.Connection = None  # type: ignore

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
        create_parser.add_argument("--network", help="Network ID or name.", type=str)
        create_parser.add_argument("--auth-url", help="Authentication URL.", type=str, required=True)
        create_parser.add_argument("--username", help="OpenStack username.", type=str, required=True)
        create_parser.add_argument("--password", help="OpenStack password.", type=str, required=True)
        create_parser.add_argument("--project-name", help="OpenStack project name.", type=str, required=True)

        # Parser for delete
        delete_parser = subparsers.add_parser("delete", help="Delete an instance.")
        delete_parser.add_argument("name", help="Name of the instance.", type=str)
        delete_parser.add_argument("--auth-url", help="Authentication URL.", type=str, required=True)
        delete_parser.add_argument("--username", help="OpenStack username.", type=str, required=True)
        delete_parser.add_argument("--password", help="OpenStack password.", type=str, required=True)
        delete_parser.add_argument("--project-name", help="OpenStack project name.", type=str, required=True)

        # Parser for show
        show_parser = subparsers.add_parser("show", help="Show details of an instance.")
        show_parser.add_argument("name", help="Name of the instance.", type=str)
        show_parser.add_argument("--auth-url", help="Authentication URL.", type=str, required=True)
        show_parser.add_argument("--username", help="OpenStack username.", type=str, required=True)
        show_parser.add_argument("--password", help="OpenStack password.", type=str, required=True)
        show_parser.add_argument("--project-name", help="OpenStack project name.", type=str, required=True)

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
                network=args.network,
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
        self, name: str, image: str, flavor: str, key_name: Optional[str] = None, network: Optional[str] = None
    ) -> Any:
        """
        🛠 Create an OpenStack EC2 instance.

        Args:
            name (str): Name of the instance.
            image (str): Image ID or name.
            flavor (str): Flavor ID or name.
            key_name (Optional[str]): Key pair name.
            network (Optional[str]): Network ID or name.
        """
        image = self.conn.compute.find_image(image)
        flavor = self.conn.compute.find_flavor(flavor)

        if network:
            network = self.conn.network.find_network(network)
            nics = [{"net-id": network.id}]  # type: ignore
        else:
            nics = None

        instance = self.conn.compute.create_server(
            name=name,
            image_id=image.id,  # type: ignore
            flavor_id=flavor.id,  # type: ignore
            key_name=key_name,
            nics=nics,
        )
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
