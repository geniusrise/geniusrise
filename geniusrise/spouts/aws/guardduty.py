# geniusrise
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

import asyncio
import logging
from typing import List

from aioboto3.session import Session

from geniusrise.data_sources.streaming import StreamingDataFetcher


class GuardDutyEventFetcher(StreamingDataFetcher):
    def __init__(self, wait: int = 600, handler=None, state_manager=None):
        super().__init__(handler, state_manager)
        self.session = Session()
        self.guardduty = self.session.create_client("guardduty")
        self.log = logging.getLogger(__name__)
        self.wait = wait

    async def listen(self):
        """
        Start listening for GuardDuty findings.
        """
        detector_ids = self.get_detector_ids()
        while True:
            for detector_id in detector_ids:
                try:
                    findings = await self.get_findings(detector_id)
                    for finding in findings:
                        self.save(finding, f"{finding['Id']}.json")
                except Exception as e:
                    self.log.error(f"Error fetching findings for detector {detector_id}: {e}")
            await asyncio.sleep(self.wait)  # wait for 60 seconds before fetching new findings

    def get_detector_ids(self) -> List[str]:
        """
        Get the list of GuardDuty detector IDs.

        :return: List of detector IDs.
        """
        response = self.guardduty.list_detectors()
        if response["DetectorIds"]:
            return response["DetectorIds"]
        else:
            self.log.warning("No GuardDuty detectors found")
            return []

    async def get_findings(self, detector_id: str) -> List[dict]:
        """
        Get the findings for a specific detector.

        :param detector_id: ID of the detector to get findings for.
        :return: List of findings.
        """
        findings = []
        paginator = self.guardduty.get_paginator("get_findings")
        try:
            for page in paginator.paginate(DetectorId=detector_id):
                findings.extend(page["Findings"])
        except Exception as e:
            self.log.error(f"Error fetching findings for detector {detector_id}: {e}")
        return findings
