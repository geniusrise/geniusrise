from typing import List

import pydantic


class FineTuningDataItem(pydantic.BaseModel):
    prompt: str
    completion: str


class FineTuningData(pydantic.BaseModel):
    data: List[FineTuningDataItem]
