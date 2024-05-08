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

import grpc
from concurrent import futures
import threading
import base64
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel, ValidationError
from grpc_interceptor import ServerInterceptor
from grpc_interceptor.exceptions import GrpcException, InvalidArgument, Unauthenticated

from authlib.integrations.requests_client import OAuth2Session


class GRPCInterface:
    def __init__(
        self,
        klass: Any,
        method_name: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        auth_method: Optional[str] = None,
        oauth_config: Optional[Dict[str, Any]] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the GRPCInterface.

        Args:
            klass (Any): The class or function to handle the API request.
            method_name (str): The name of the method to execute from the klass.
            input_schema (Type[BaseModel]): The Pydantic input schema for request validation.
            output_schema (Type[BaseModel]): The Pydantic output schema for response validation.
            auth_method (str, optional): The authentication method to use. Can be "basic" or "oauth". Defaults to "basic".
            oauth_config (Optional[Dict[str, Any]], optional): The OAuth configuration if auth_method is "oauth". Defaults to None.
            username (Optional[str], optional): The username for basic authentication. Defaults to None.
            password (Optional[str], optional): The password for basic authentication. Defaults to None.
        """
        self.klass = klass
        self.method_name = method_name
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.auth_method = auth_method
        self.oauth_config = oauth_config
        self.username = username
        self.password = password

        # Define a global lock for sequential access control
        self.sequential_lock = threading.Lock()

    def _authenticate_basic(self, context: grpc.ServicerContext) -> bool:
        """
        Authenticate the request using basic authentication.

        Args:
            context (grpc.ServicerContext): The gRPC servicer context.

        Returns:
            bool: True if the request is authenticated, False otherwise.

        Raises:
            Unauthenticated: If the authentication fails.
        """
        metadata = dict(context.invocation_metadata())
        if "authorization" not in metadata:
            raise Unauthenticated("Missing authorization header")

        authorization = metadata["authorization"]
        if not authorization.startswith("Basic "):
            raise Unauthenticated("Invalid authorization header")

        encoded_credentials = authorization.split(" ")[1]
        decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8")
        username, password = decoded_credentials.split(":")

        if username != self.username or password != self.password:
            raise Unauthenticated("Invalid credentials")

        return True

    def _authenticate_oauth(self, context: grpc.ServicerContext) -> bool:
        """
        Authenticate the request using OAuth.

        Args:
            context (grpc.ServicerContext): The gRPC servicer context.

        Returns:
            bool: True if the request is authenticated, False otherwise.

        Raises:
            Unauthenticated: If the authentication fails.
        """
        metadata = dict(context.invocation_metadata())
        if "authorization" not in metadata:
            raise Unauthenticated("Missing authorization header")

        authorization = metadata["authorization"]
        if not authorization.startswith("Bearer "):
            raise Unauthenticated("Invalid authorization header")

        access_token = authorization.split(" ")[1]

        if self.oauth_config:
            client_id = self.oauth_config["client_id"]
            client_secret = self.oauth_config["client_secret"]
            token_url = self.oauth_config["token_url"]

        session = OAuth2Session(client_id, client_secret)
        token_info = session.fetch_token(token_url, grant_type="client_credentials")

        if access_token != token_info["access_token"]:
            raise Unauthenticated("Invalid access token")

        return True

    def _authenticate_request(self, context: grpc.ServicerContext) -> bool:
        """
        Authenticate the request using the specified authentication method.

        Args:
            context (grpc.ServicerContext): The gRPC servicer context.

        Returns:
            bool: True if the request is authenticated, False otherwise.

        Raises:
            Unauthenticated: If the authentication fails.
        """
        if self.auth_method is None or self.auth_method.lower() == "none":
            return True
        elif self.auth_method == "basic":
            return self._authenticate_basic(context)
        elif self.auth_method == "oauth":
            return self._authenticate_oauth(context)
        else:
            raise ValueError("Invalid authentication method. Supported methods: 'basic', 'oauth'")

    def serve(self, port: int, max_workers: int = 10, concurrent_queries: bool = False) -> None:
        """
        Start the gRPC server and listen for requests.

        Args:
            port (int): The port number to listen on.
            max_workers (int, optional): The maximum number of worker threads. Defaults to 10.
            concurrent_queries (bool, optional): Whether to allow concurrent queries. Defaults to False.
        """
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), interceptors=[ErrorInterceptor()])
        server.add_insecure_port(f"[::]:{port}")

        def handle_request(request: Dict[str, Any], context: grpc.ServicerContext) -> Dict[str, Any]:
            if not self._authenticate_request(context):
                raise Unauthenticated("Authentication failed")

            if not concurrent_queries:
                self.sequential_lock.acquire()

            try:
                validated_request = self.input_schema(**request).dict()
                response = self.klass(self.method_name, **validated_request)
                validated_response = self.output_schema(**response).dict()
                return validated_response
            except ValidationError as e:
                raise InvalidArgument(str(e))
            finally:
                if not concurrent_queries:
                    self.sequential_lock.release()

        server.start()
        server.wait_for_termination()


class ErrorInterceptor(ServerInterceptor):
    def intercept(self, method, request, context, method_name):
        try:
            return method(request, context)
        except GrpcException as e:
            context.set_code(e.status_code)
            context.set_details(str(e))
            raise
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(e))
            raise
