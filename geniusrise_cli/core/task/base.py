from abc import ABC, abstractmethod


class Task(ABC):
    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def destroy(self):
        pass

    @abstractmethod
    def get_status(self):
        pass

    @abstractmethod
    def get_statistics(self):
        pass

    @abstractmethod
    def get_logs(self):
        pass
