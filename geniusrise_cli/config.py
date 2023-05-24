import os

import direnv  # type: ignore

direnv.load()


ENV = os.environ.get("ENV", "dev")
LOGLEVEL = os.environ.get("LOGLEVEL", "DEBUG")

# OpenAI settings
OPENAI_ORGANIZATION = os.environ.get("OPENAI_ORGANIZATION", None)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_API_TYPE = os.environ.get("OPENAI_API_TYPE", "open_ai")
OPENAI_API_BASE_URL = os.environ.get("OPENAI_API_BASE_URL", "https://api.openai.com/v1")
OPENAI_API_VERSION = os.environ.get(
    "OPENAI_API_VERSION",
    ("2023-03-15-preview" if OPENAI_API_TYPE in ("azure", "azure_ad", "azuread") else None),
)

# Google PALM settings
PALM_KEY = os.environ.get("PALM_KEY", "")

# Data sources

GITHUB_ACCESS_TOKEN = os.environ.get("GITHUB_ACCESS_TOKEN", "")
