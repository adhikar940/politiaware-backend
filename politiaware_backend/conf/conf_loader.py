import os
import tomli
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Get ENVIRONMENT (default: local)
ENVIRONMENT = os.getenv("ENVIRONMENT", "local").lower()

# Map environment -> config file
config_map = {
    "local": "local.toml",
    "dev": "dev.toml",
    "prod": "prod.toml",
}

# Pick the correct config file
config_file = config_map.get(ENVIRONMENT, "local.toml")

# Build full path
BASE_DIR = os.path.dirname(__file__) 
CONFIG_PATH = os.path.join(BASE_DIR, config_file)

# Load config
with open(CONFIG_PATH, "rb") as f:
    raw_config = tomli.load(f)


def resolve_value(value: str):
    """Replace env:VAR with os.environ[VAR]."""
    if isinstance(value, str) and value.startswith("env:"):
        return os.getenv(value.split(":", 1)[1])
    return value


def resolve_config(d: dict):
    """Recursively resolve values."""
    resolved = {}
    for k, v in d.items():
        if isinstance(v, dict):
            resolved[k] = resolve_config(v)
        elif isinstance(v, list):
            resolved[k] = [resolve_value(i) for i in v]
        else:
            resolved[k] = resolve_value(v)
    return resolved


# Final resolved config
config = resolve_config(raw_config)

