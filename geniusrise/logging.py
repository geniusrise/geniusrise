# 🧠 Geniusrise
# Copyright (C) 2023  geniusrise.ai
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
from typing import Optional

import colorlog
import os

from geniusrise.core.state import State


LOGLEVEL = os.getenv("LOGLEVEL", "INFO")


# class StateHandler(logging.Handler):
#     """
#     🛠️ **StateHandler**: Handler for logging state changes.

#     This class is used to capture logging via state module in geniusrise.
#     """

#     def __init__(self, state_instance: State):
#         super().__init__()
#         self.state = state_instance

#     def emit(self, record: Any):
#         log_entry = self.format(record)
#         self.state.capture_log(log_entry)


def setup_logger(state_instance: Optional[State] = None) -> logging.Logger:
    """
    🛠️ **Setup Logger**: Configure and return a logger with a default ColoredFormatter.

    This function sets up a logger for the `geniusrise-cli` with colorful logging outputs. The log level is determined by the `LOGLEVEL` from the configuration.

    ## Usage:
    ```python
    logger = setup_logger()
    logger.info("This is a fancy info log!")
    ```

    Returns:
        logging.Logger: Configured logger with colorful outputs.
    """
    # Define the custom formatter
    formatter = (
        colorlog.ColoredFormatter(
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(yellow)s[%(asctime)s] "
            "%(blue)s[%(name)s:%(lineno)d] "
            "%(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
        if logging.getLevelName(LOGLEVEL) < logging.INFO
        else colorlog.ColoredFormatter(
            "%(log_color)-8s%(reset)s %(log_color)s%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            reset=True,
            log_colors={
                "DEBUG": "white",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            },
        )
    )

    # Suppress kafka library info logs
    if logging.getLevelName(LOGLEVEL) < logging.INFO:
        logger = logging.getLogger("kafka")
        logger.setLevel(logging.WARN)

    # Setup logger for geniusrise
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # if state_instance:
    #     state_handler = StateHandler(state_instance)
    #     state_handler.setFormatter(formatter)

    logging.basicConfig(encoding="utf-8", level=logging.getLevelName(LOGLEVEL), handlers=[handler])
    logger = logging.getLogger("geniusrise")
    logger.setLevel(logging.getLevelName(LOGLEVEL))

    return logger
