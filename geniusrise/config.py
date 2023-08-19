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

import os

import direnv  # type: ignore

direnv.load()


ENV = os.environ.get("ENV", "dev")
LOGLEVEL = os.environ.get("LOGLEVEL", "INFO")

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
