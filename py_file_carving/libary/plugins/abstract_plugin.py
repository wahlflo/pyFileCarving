import logging
import re
from abc import ABC, abstractmethod

from py_file_carving.libary.worker import AbstractWorker

logger = logging.getLogger(__name__)


class AbstractPlugin(ABC):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        self.file_writer = file_writer
        self.make_corruption_checks = make_corruption_checks
        self.flush_if_maximum_file_size_is_reached = flush_if_maximum_file_size_is_reached
        self.triggered_indexes = set()
        self.pattern_trigger_sequence = list()

    def check_for_trigger_sequence(self, index_offset: int, search_data: bytes):
        new_workers = list()
        for pattern in self.pattern_trigger_sequence:
            new_indexes = [m.start(0) for m in re.finditer(pattern, search_data)]
            for x in new_indexes:
                if not self.__was_already_triggered(
                        new_index=index_offset + x):  # prevents that a trigger triggers more than one time
                    new_worker = self.create_worker(first_chunk=search_data[x:])
                    new_worker.file_writer = self.file_writer
                    new_worker.start_index = index_offset + x
                    new_workers.append(new_worker)
        return new_workers

    @abstractmethod
    def create_worker(self, first_chunk: bytes) -> AbstractWorker:
        pass

    def __was_already_triggered(self, new_index: int) -> bool:
        if new_index in self.triggered_indexes:
            return True
        self.triggered_indexes.add(new_index)
        return False
