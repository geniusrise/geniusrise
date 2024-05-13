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

from geniusrise.runners.openstack.instance import OpenStackInstanceRunner
from argparse import ArgumentParser, Namespace


class AceCloudInstanceRunner(OpenStackInstanceRunner):
    r"""
    🚀 Initialize the AceCloudInstanceRunner class for managing Ace cloud EC2 instances.

    CLI Usage:
        genius acecloud [sub-command] [options]
        Examples:

        ```bash
        genius acecloud create --name example-instance --image ubuntu --flavor m1.small --key-name mykey --network my-network \
            --block-storage-size 10 --open-ports 80,443 --user-data "#!/bin/bash\napt-get update\napt-get install -y apache2" \
            --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius acecloud delete --name example-instance \
            --username myuser --password mypassword --project-name myproject
        ```

        ```bash
        genius acecloud show --name example-instance \
            --username myuser --password mypassword --project-name myproject
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
        parser.add_argument("--username", help="Ace cloud username.", type=str, required=True)
        parser.add_argument("--password", help="Ace cloud password.", type=str, required=True)
        parser.add_argument("--project-name", help="Ace cloud project name.", type=str, required=True)
        # fmt: on
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        """
        🎛 Create a parser for CLI commands related to Ace cloud EC2 functionalities.

        Args:
            parser (ArgumentParser): The main parser.

        Returns:
            ArgumentParser: The parser with subparsers for each command.
        """
        subparsers = parser.add_subparsers(dest="acecloud")

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
        🚀 Run the Ace cloud EC2 manager.

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
                allocate_ip=args.allocate_ip,
                network=args.network,
                block_storage_size=args.block_storage_size,
                open_ports=args.open_ports,
                user_data=args.user_data,
            )
        elif args.acecloud == "delete":
            self.delete(name=args.name)
        elif args.acecloud == "show":
            self.status(name=args.name)
        else:
            raise ValueError(f"Unknown command: {args.acecloud}")
