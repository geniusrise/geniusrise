import pydantic
from typing import List


class FineTuningDataItem(pydantic.BaseModel):
    prompt: str
    completion: str


class FineTuningData(pydantic.BaseModel):
    data: List[FineTuningDataItem]
