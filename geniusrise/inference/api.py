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

import json
from typing import Any, Dict, Optional, Type
import threading

import cherrypy
from authlib.integrations.requests_client import OAuth2Session
from pydantic import BaseModel, ValidationError


@cherrypy.expose
class APIInterface:
    def __init__(
        self,
        path: str,
        klass: Any,
        method_name: str,
        input_schema: Type[BaseModel],
        output_schema: Type[BaseModel],
        auth_method: Optional[str] = None,
        oauth_config: Optional[Dict[str, Any]] = None,
        concurrent_queries: bool = False,
        endpoint: str = "*",
        port: int = 3000,
        cors_domain: str = "http://localhost:3000",
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the APIInterface.

        Args:
            path (str): The API endpoint path.
            klass (Any): The class or function to handle the API request.
            method_name (str): The name of the method to execute from the klass.
            input_schema (Type[BaseModel]): The Pydantic input schema for request validation.
            output_schema (Type[BaseModel]): The Pydantic output schema for response validation.
            auth_method (str, optional): The authentication method to use. Can be "basic" or "oauth". Defaults to "basic".
            oauth_config (Optional[Dict[str, Any]], optional): The OAuth configuration if auth_method is "oauth". Defaults to None.
            concurrent_queries (bool, optional): Whether the API supports concurrent API calls. Defaults to False.
            endpoint (str, optional): The endpoint to listen on. Defaults to "*".
            port (int, optional): The port to listen on. Defaults to 3000.
            cors_domain (str, optional): The domain to allow CORS requests from. Defaults to "http://localhost:3000".
            username (Optional[str], optional): The username to use for basic authentication. Defaults to None.
            password (Optional[str], optional): The password to use for basic authentication. Defaults to None.
        """
        self.path = path
        self.klass = klass
        self.method_name = method_name
        self.input_schema = input_schema
        self.output_schema = output_schema
        self.auth_method = auth_method
        self.oauth_config = oauth_config
        self.concurrent_queries = concurrent_queries
        self.endpoint = endpoint
        self.port = port
        self.cors_domain = cors_domain
        self.username = username
        self.password = password

        # Define a global lock for sequential access control
        self.sequential_lock = threading.Lock()

        self.__start()

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Handle POST requests.

        Returns:
            Dict[str, Any]: The validated output data.
        """
        return self.__handle_request(*args, **kwargs)

    @cherrypy.tools.accept(media="text/plain")
    def GET(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Handle GET requests.

        Returns:
            Dict[str, Any]: The validated output data.
        """
        return self.__handle_request(*args, **kwargs)

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def PUT(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Handle PUT requests.

        Returns:
            Dict[str, Any]: The validated output data.
        """
        return self.__handle_request(*args, **kwargs)

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def DELETE(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Handle DELETE requests.

        Returns:
            Dict[str, Any]: The validated output data.
        """
        return self.__handle_request(*args, **kwargs)

    def __handle_request(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Handle the API request.

        Returns:
            Dict[str, Any]: The validated output data.
        """
        try:
            # Validate the input data against the input schema
            input_data = self.input_schema(**cherrypy.request.json).dict()

            # Call the handler function with the validated input data
            output_data = self.klass(self.method_name, **input_data)

            # Validate the output data against the output schema
            validated_output = self.output_schema(**output_data)

            # Return the validated output data
            return validated_output.dict()

        except ValidationError as e:
            # Handle validation errors
            cherrypy.response.status = 400
            return {"error": str(e)}

        except Exception as e:
            # Handle other exceptions
            cherrypy.response.status = 500
            return {"error": str(e)}

    def __validate_password(self, realm: str, username: str, password: str) -> bool:
        """
        Validate the username and password against expected values.

        Args:
            realm (str): The authentication realm.
            username (str): The provided username.
            password (str): The provided password.

        Returns:
            bool: True if credentials are valid, False otherwise.
        """
        return username == self.username and password == self.password

    def __validate_oauth_token(self, token: str) -> bool:
        """
        Validate the OAuth token.

        Args:
            token (str): The OAuth token.

        Returns:
            bool: True if the token is valid, False otherwise.
        """
        if not self.oauth_config:
            return False

        client_id = self.oauth_config["client_id"]
        client_secret = self.oauth_config["client_secret"]
        token_url = self.oauth_config["token_url"]

        session = OAuth2Session(client_id, client_secret)
        token_info = session.fetch_token(token_url, grant_type="client_credentials")
        return token_info["access_token"] == token

    def __start(self) -> None:
        """
        Start a CherryPy server to listen for requests.
        """

        def sequential_locker():
            if self.concurrent_queries:
                self.sequential_lock.acquire()

        def sequential_unlocker():
            if self.concurrent_queries:
                self.sequential_lock.release()

        def CORS():
            cherrypy.response.headers["Access-Control-Allow-Origin"] = self.cors_domain
            cherrypy.response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            cherrypy.response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
            cherrypy.response.headers["Access-Control-Allow-Credentials"] = "true"

            if cherrypy.request.method == "OPTIONS":
                cherrypy.response.status = 200
                return True

        cherrypy.config.update(
            {
                "server.socket_host": "0.0.0.0",
                "server.socket_port": self.port,
                "log.screen": False,
                "tools.CORS.on": True,
                "error_page.400": error_page,
                "error_page.401": error_page,
                "error_page.402": error_page,
                "error_page.403": error_page,
                "error_page.404": error_page,
                "error_page.405": error_page,
                "error_page.406": error_page,
                "error_page.408": error_page,
                "error_page.415": error_page,
                "error_page.429": error_page,
                "error_page.500": error_page,
                "error_page.501": error_page,
                "error_page.502": error_page,
                "error_page.503": error_page,
                "error_page.504": error_page,
                "error_page.default": error_page,
            }
        )

        conf: dict
        if self.auth_method is None:
            # Configuration without authentication
            conf = {
                "/": {
                    "tools.sequential_locker.on": True,
                    "tools.sequential_unlocker.on": True,
                    "tools.CORS.on": True,
                }
            }
        elif self.auth_method == "basic":
            if self.username and self.password:
                # Configure basic authentication
                conf = {
                    "/": {
                        "tools.sequential_locker.on": True,
                        "tools.sequential_unlocker.on": True,
                        "tools.auth_basic.on": True,
                        "tools.auth_basic.realm": "geniusrise",
                        "tools.auth_basic.checkpassword": self.__validate_password,
                        "tools.CORS.on": True,
                    }
                }
            else:
                raise ValueError("Basic auth needs username and password")
        elif self.auth_method == "oauth":
            # Configure OAuth authentication
            conf = {
                "/": {
                    "tools.sequential_locker.on": True,
                    "tools.sequential_unlocker.on": True,
                    "tools.auth_oauth.on": True,
                    "tools.auth_oauth.realm": "geniusrise",
                    "tools.auth_oauth.checktoken": self.__validate_oauth_token,
                    "tools.CORS.on": True,
                }
            }
        else:
            raise ValueError("Invalid authentication method. Supported methods: 'basic', 'oauth'")

        cherrypy.tools.sequential_locker = cherrypy.Tool("before_handler", sequential_locker)
        cherrypy.tools.CORS = cherrypy.Tool("before_handler", CORS)
        cherrypy.tools.auth_oauth = cherrypy._cptools.HandlerTool(self.__validate_oauth_token)
        cherrypy.tree.mount(self, self.path, conf)
        cherrypy.tools.CORS = cherrypy.Tool("before_finalize", CORS)
        cherrypy.tools.sequential_unlocker = cherrypy.Tool("before_finalize", sequential_unlocker)
        cherrypy.engine.start()
        cherrypy.engine.block()


def error_page(status: int, message: str, traceback: str, version: str) -> str:
    """
    Generate an error response.

    Args:
        status (int): The HTTP status code.
        message (str): The error message.
        traceback (str): The error traceback.
        version (str): The CherryPy version.

    Returns:
        str: The JSON-encoded error response.
    """
    response = {
        "status": status,
        "message": message,
    }
    return json.dumps(response)
