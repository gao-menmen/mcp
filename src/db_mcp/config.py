"""Configuration loading for db-mcp."""

import json
import os
from pathlib import Path


def load_config() -> dict:
    """Load MCP server config from MCP_CONFIG_PATH env var or ./config.json.

    Returns an empty dict if no config file exists.
    """
    env_path = os.environ.get("MCP_CONFIG_PATH")
    if env_path:
        config_path = Path(env_path)
    else:
        config_path = Path("./config.json")

    if not config_path.exists():
        return {}

    return json.loads(config_path.read_text(encoding="utf-8"))
