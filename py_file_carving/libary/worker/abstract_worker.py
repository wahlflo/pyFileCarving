from abc import ABC, abstractmethod


class AbstractWorker(ABC):
    def __init__(self, first_chunk: bytes, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        self.file_writer = None
        self.start_index = None
        self.data = first_chunk
        self.make_corruption_checks = make_corruption_checks
        self.flush_if_maximum_file_size_is_reached = flush_if_maximum_file_size_is_reached

    @abstractmethod
    def update(self, new_data_chunk: bytes) -> bool:
        """ returns True if object continues living otherwise False """
        pass

    def end_of_data_signal(self):
        self.update(new_data_chunk=bytes())
