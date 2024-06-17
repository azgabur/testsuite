"""
Kuadrant configuration command line utility

Usage:
  kuadrantctl [command]

Available Commands:
  completion  Generate the autocompletion script for the specified shell
  generate    Commands related to kubernetes object generation
    gatewayapi  Generate Gataway API resources
        httproute   Generate Gateway API HTTPRoute from OpenAPI 3.0.X
    kuadrant    Generate Kuadrant resources
        authpolicy      Generate Kuadrant AuthPolicy from OpenAPI 3.0.X
        ratelimitpolicy Generate Kuadrant Rate Limit Policy from OpenAPI 3.0.X


  help        Help about any command
  version     Print the version number of kuadrantctl

Flags:
  -h, --help                   help for httproute
      --oas string             Path to OpenAPI spec file (in JSON or YAML format), URL, or '-' to read from standard input (required)
  -o, --output-format string   Output format: 'yaml' or 'json'. (default "yaml")

Global Flags:
  -v, --verbose   verbose output


Use "kuadrantctl [command] --help" for more information about a command.

"""

import shutil
import subprocess
import json
from functools import cached_property
from typing import Optional, Literal

from testsuite.gateway.gateway_api.route import HTTPRoute
from testsuite.policy.rate_limit_policy import RateLimitPolicy
from testsuite.policy.authorization.auth_policy import AuthPolicy


class KuadrantctlException(Exception):
    """Exception raised by Kuadrantctl client"""


class KuadrantctlClient:
    """The doc string"""

    def __init__(self, binary, openshift) -> None:
        super().__init__()
        self.binary = binary
        self.openshift = openshift

    @cached_property
    def exists(self) -> bool:
        """Returns true if the binary exists and is correctly set up"""
        return bool(shutil.which(self.binary))

    @cached_property
    def version(self) -> dict[str, str]:
        return self._execute_command("version").stdout

    def generate_httproute(self, oas: str) -> HTTPRoute:
        return HTTPRoute(self._generate(oas, "httproute"))

    def generate_authpolicy(self, oas: str) -> AuthPolicy:
        return AuthPolicy(self._generate(oas, "authpolicy"))

    def generate_ratelimit(self, oas: str) -> RateLimitPolicy:
        return RateLimitPolicy(self._generate(oas, "ratelimitpolicy"))

    def _generate(self, oas: str, obj_cls: Literal["httproute", "authpolicy", "ratelimitpolicy"]):
        command = ""
        match obj_cls:
            case "httproute":
                command = "gatewayapi httproute"
            case "authpolicy":
                command = "kuadrant authpolicy"
            case "ratelimitpolicy":
                command = "kuadrant ratelimitpolicy"

        return self._execute_command(f"generate {command} -o yaml --oas -", stdin=oas).stdout

    def _execute_command(
        self, command_line: str, stdin: Optional[str] = None, env: Optional[dict[str, str]] = None
    ):
        args = (self.binary, command_line.split())
        try:
            response = subprocess.run(
                args,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                input=stdin,
                universal_newlines=bool(stdin),
                check=False,
                env=env,
            )
            if response.returncode != 0:
                """Maybe not needed? We surely want to test error-handeling."""
                raise KuadrantctlException(f"kuadrantctl returned non-zero return code. Stderr:\n {response.stderr}")
            return response
        except Exception as exception:
            # If some error occurs, first check if the binary exists to throw better error
            if not self.exists:
                raise AttributeError("Kuadrantctl binary does not exist") from exception
            raise exception
