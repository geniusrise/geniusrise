from abc import ABC, abstractmethod
from typing import Dict, Any


class Task(ABC):
    @abstractmethod
    def run(self) -> None:
        pass

    @abstractmethod
    def destroy(self) -> None:
        pass

    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_logs(self) -> Dict[str, Any]:
        pass
