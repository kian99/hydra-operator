# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.

"""A helper class for interacting with the hydra CLI."""


import json
import logging
from typing import Dict, List, Optional, Tuple, Union

from ops.model import Container

logger = logging.getLogger(__name__)
SUPPORTED_SCOPES = ["openid", "profile", "email", "phone"]


class HydraCLI:
    """Helper object for running hydra CLI commands."""

    def __init__(self, hydra_admin_url: str, container: Container):
        self.hydra_admin_url = hydra_admin_url
        self.container = container

    def _dump_list(self, data: Optional[List]) -> str:
        if not data:
            return ""
        return (",").join(data)

    def _dump_dict(self, data: Optional[Dict]) -> str:
        if not data:
            return ""
        return json.dumps(data, separators=(",", ":"))

    def _build_client_cmd_flags(
        self,
        audience: Optional[List[str]] = None,
        grant_type: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        response_type: Optional[List[str]] = None,
        scope: List[str] = SUPPORTED_SCOPES,
        client_secret: Optional[str] = None,
        token_endpoint_auth_method: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> List[str]:
        """Convert a ClientConfig object to a list of parameters."""
        flag_mapping = {
            "--audience": self._dump_list(audience),
            "--grant-type": self._dump_list(grant_type),
            "--redirect-uri": redirect_uri,
            "--response-type": self._dump_list(response_type),
            "--secret": client_secret,
            "--token-endpoint-auth-method": token_endpoint_auth_method,
            "--metadata": self._dump_dict(metadata),
        }
        flags = []

        for k, v in flag_mapping.items():
            if v:
                flags.append(k)
                flags.append(v)

        if scope:
            for s in scope:
                flags.append("--scope")
                flags.append(s)
        return flags

    def _client_cmd_prefix(self, action: str) -> List[str]:
        return [
            "hydra",
            action,
            "client",
            "--endpoint",
            self.hydra_admin_url,
            "--format",
            "json",
        ]

    def create_client(
        self,
        audience: Optional[List[str]] = None,
        grant_type: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        response_type: Optional[List[str]] = ["code"],
        scope: List[str] = SUPPORTED_SCOPES,
        client_secret: Optional[str] = None,
        token_endpoint_auth_method: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Create an oauth2 client."""
        cmd = self._client_cmd_prefix("create") + self._build_client_cmd_flags(
            audience=audience,
            grant_type=grant_type,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            client_secret=client_secret,
            token_endpoint_auth_method=token_endpoint_auth_method,
            metadata=metadata,
        )

        stdout, _ = self._run_cmd(cmd)
        json_stdout = json.loads(stdout)
        logger.info(f"Successfully created client: {json_stdout.get('client_id')}")
        return json_stdout

    def get_client(self, client_id: str) -> Dict:
        """Get an oauth2 client."""
        cmd = self._client_cmd_prefix("get")
        cmd.append(client_id)

        stdout, _ = self._run_cmd(cmd)
        logger.info(f"Successfully fetched client: {client_id}")
        return json.loads(stdout)

    def update_client(
        self,
        client_id: str,
        audience: Optional[List[str]] = None,
        grant_type: Optional[List[str]] = None,
        redirect_uri: Optional[str] = None,
        response_type: Optional[List[str]] = ["code"],
        scope: List[str] = SUPPORTED_SCOPES,
        client_secret: Optional[str] = None,
        token_endpoint_auth_method: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """Update an oauth2 client."""
        cmd = self._client_cmd_prefix("update") + self._build_client_cmd_flags(
            audience=audience,
            grant_type=grant_type,
            redirect_uri=redirect_uri,
            response_type=response_type,
            scope=scope,
            client_secret=client_secret,
            token_endpoint_auth_method=token_endpoint_auth_method,
            metadata=metadata,
        )
        cmd.append(client_id)

        stdout, _ = self._run_cmd(cmd)
        logger.info(f"Successfully updated client: {client_id}")
        return json.loads(stdout)

    def delete_client(self, client_id: str) -> str:
        """Delete an oauth2 client."""
        cmd = self._client_cmd_prefix("delete")
        cmd.append(client_id)

        stdout, _ = self._run_cmd(cmd)
        logger.info(f"Successfully deleted client: {stdout}")
        return json.loads(stdout)

    def list_clients(self) -> Dict:
        """Delete one or more oauth2 client."""
        cmd = [
            "hydra",
            "list",
            "clients",
            "--endpoint",
            self.hydra_admin_url,
            "--format",
            "json",
        ]

        stdout, _ = self._run_cmd(cmd)
        logger.info("Successfully listed clients")
        return json.loads(stdout)

    def delete_client_access_tokens(self, client_id: str) -> str:
        """Delete one or more oauth2 client."""
        cmd = [
            "hydra",
            "delete",
            "access-tokens",
            "--endpoint",
            self.hydra_admin_url,
            "--format",
            "json",
            client_id,
        ]

        stdout, _ = self._run_cmd(cmd)
        logger.info(f"Successfully deleted all the access tokens for client: {stdout}")
        return json.loads(stdout)

    def create_jwk(self, set_id: str = "hydra.openid.id-token", alg: str = "RS256") -> Dict:
        """Add a new key to a jwks."""
        cmd = [
            "hydra",
            "create",
            "jwk",
            "--endpoint",
            self.hydra_admin_url,
            "--format",
            "json",
            "--alg",
            alg,
            set_id,
        ]

        stdout, _ = self._run_cmd(cmd)
        json_stdout = json.loads(stdout)
        logger.info(f"Successfully created jwk: {json_stdout['keys'][0]['kid']}")
        return json_stdout

    def _run_cmd(
        self, cmd: List[str], timeout: float = 20
    ) -> Tuple[Union[str, bytes], Union[str, bytes]]:
        logger.debug(f"Running cmd: {cmd}")
        process = self.container.exec(cmd, timeout=timeout)
        stdout, stderr = process.wait_output()
        return stdout, stderr
