import logging
from argparse import ArgumentParser, Namespace
import requests
import json


class VastResourceManager:
    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)
        self.api_key = None  # type: Optional[str]

    def _add_connection_args(self, parser: ArgumentParser) -> ArgumentParser:
        parser.add_argument("--api_key", help="API key for Vast.AI.", type=str, required=True)
        return parser

    def create_parser(self, parser: ArgumentParser) -> ArgumentParser:
        subparsers = parser.add_subparsers(dest="command")

        # Parser for creating an instance
        create_parser = subparsers.add_parser("create", help="Create a new instance.")
        create_parser.add_argument("offer_id", help="ID of the offer.", type=str)
        create_parser = self._add_connection_args(create_parser)

        # Parser for stopping an instance
        stop_parser = subparsers.add_parser("stop", help="Stop an instance.")
        stop_parser.add_argument("instance_id", help="ID of the instance.", type=str)
        stop_parser = self._add_connection_args(stop_parser)

        # Parser for terminating an instance
        terminate_parser = subparsers.add_parser("terminate", help="Terminate an instance.")
        terminate_parser.add_argument("instance_id", help="ID of the instance.", type=str)
        terminate_parser = self._add_connection_args(terminate_parser)

        # Parser for getting instances
        get_instances_parser = subparsers.add_parser("get_instances", help="Get all instances.")
        get_instances_parser = self._add_connection_args(get_instances_parser)

        # Parser for status
        status_parser = subparsers.add_parser("status", help="Get the status of an instance.")
        status_parser.add_argument("instance_id", help="ID of the instance.", type=str)
        status_parser = self._add_connection_args(status_parser)

        return parser

    def run(self, args: Namespace) -> None:
        self.api_key = args.api_key  # Set the API key from arguments

        if args.command == "create":
            self.create_instance(args.offer_id)
        elif args.command == "stop":
            self.stop_instance(args.instance_id)
        elif args.command == "terminate":
            self.terminate_instance(args.instance_id)
        elif args.command == "get_instances":
            self.get_instances()
        elif args.command == "status":
            self.status(args.instance_id)
        else:
            self.log.exception("Unknown command: %s", args.command)

    def status(self, machine_id: str) -> None:
        req_url = f"https://api.vast.ai/machines?owner=me&api_key={self.api_key}"
        r = requests.get(req_url)
        r.raise_for_status()
        rows = r.json()["machines"]
        for machine in rows:
            if machine["id"] == machine_id:
                self.log.info(f"Machine ID: {machine['id']}, Status: {json.dumps(machine, indent=4, sort_keys=True)}")

    def create_instance(self, offer_id: str) -> None:
        payload = {"offer_id": offer_id}
        response = requests.post(
            f"https://vast.ai/api/v0/instances/", json=payload, headers={"Authorization": f"Bearer {self.api_key}"}
        )
        instance = response.json()
        self.log.info(f"Instance created. ID: {instance['id']}")

    def get_instances(self) -> None:
        req_url = f"https://api.vast.ai/instances?owner=me&api_key={self.api_key}"
        r = requests.get(req_url)
        r.raise_for_status()
        rows = r.json()["instances"]
        for row in rows:
            self.log.info(f"Instance ID: {row['id']}, Status: {json.dumps(row, indent=4, sort_keys=True)}")

    def stop_instance(self, instance_id: str) -> None:
        response = requests.post(
            f"https://vast.ai/api/v0/instances/{instance_id}/stop/", headers={"Authorization": f"Bearer {self.api_key}"}
        )
        self.log.info(f"Stopped instance {instance_id}")

    def terminate_instance(self, instance_id: str) -> None:
        response = requests.post(
            f"https://vast.ai/api/v0/instances/{instance_id}/terminate/",
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        self.log.info(f"Terminated instance {instance_id}")
