import configparser
import os

import swagger_client


class ClientUtils:
    cp_url = None
    username = None
    token = None
    initialized = False

    @staticmethod
    def set_client_config(url: str, user: str, tok: str):
        ClientUtils.cp_url = url
        ClientUtils.username = user
        ClientUtils.token = tok

    @staticmethod
    def get_client():
        if (
            ClientUtils.cp_url is None
            or ClientUtils.username is None
            or ClientUtils.token is None
        ):
            raise ValueError(
                "Client configuration not set. Call set_client_config first."
            )

        configuration = swagger_client.Configuration()
        configuration.username = ClientUtils.username
        configuration.password = ClientUtils.token
        configuration.host = ClientUtils.cp_url
        return swagger_client.ApiClient(configuration)

    @staticmethod
    def initialize():
        """
        Initialize configuration from environment variables or a credentials file.
        Ensures the control plane URL has https:// prefix and no trailing slash.

        Returns:
            tuple: containing cp_url, username, token, and profile.

        Raises:
            ValueError: If profile is not specified or if required credentials are missing.
        """
        profile = os.getenv("FACETS_PROFILE", "default")
        cp_url = os.getenv("CONTROL_PLANE_URL", "")
        username = os.getenv("FACETS_USERNAME", "")
        token = os.getenv("FACETS_TOKEN", "")

        if profile and not (cp_url and username and token):
            # Assume credentials exist in ~/.facets/credentials
            config = configparser.ConfigParser()
            config.read(os.path.expanduser("~/.facets/credentials"))

            if config.has_section(profile):
                cp_url = config.get(profile, "control_plane_url", fallback=cp_url)
                username = config.get(profile, "username", fallback=username)
                token = config.get(profile, "token", fallback=token)
            else:
                raise ValueError(f"Profile '{profile}' not found in credentials file.")

        if not (cp_url and username and token):
            raise ValueError("Control plane URL, username, and token are required.")

        # Ensure cp_url has https:// prefix
        if cp_url and not (
            cp_url.startswith("http://") or cp_url.startswith("https://")
        ):
            cp_url = f"https://{cp_url}"

        # Remove trailing slash if present
        if cp_url and cp_url.endswith("/"):
            cp_url = cp_url.rstrip("/")

        ClientUtils.set_client_config(cp_url, username, token)
        ClientUtils.initialized = True
        return cp_url, username, token, profile
