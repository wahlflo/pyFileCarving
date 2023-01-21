import re

from .abstract_worker import AbstractWorker


class WorkerMaximalSizeTerminating(AbstractWorker):
    def __init__(self, file_extension: str, first_chunk: bytes, footer_sequence: bytes, maximal_size_in_bytes: int,
                 make_corruption_checks: bool, flush_if_maximum_file_size_is_reached=False, minimum_bytes=None,
                 corruption_check=None):
        super().__init__(first_chunk=first_chunk, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.footer_sequence = re.compile(footer_sequence)
        self.file_extension = file_extension
        self.maximal_size_in_bytes = maximal_size_in_bytes
        self.minimum_bytes = minimum_bytes
        self.corruption_check = corruption_check
        self.already_carved = set()
        self.last_chunk = first_chunk

    def update(self, new_data_chunk: bytes) -> bool:
        """ returns True if object continues living otherwise False """

        last_two_chunks = self.last_chunk + new_data_chunk
        index_offset = len(self.data) - len(self.last_chunk)

        self.data += new_data_chunk
        self.last_chunk = new_data_chunk

        for m in re.finditer(re.compile(b'%EOF\r\n'), last_two_chunks):
            end_index = index_offset + m.end(0)

            if end_index not in self.already_carved:
                self.already_carved.add(end_index)
                if self.__check_on_corruption(content=self.data[:end_index]):
                    self.file_writer.submit_carved_file(content=self.data[:end_index],
                                                        file_extension=self.file_extension)

        if self.maximal_size_in_bytes is not None and len(self.data) > self.maximal_size_in_bytes:
            if self.flush_if_maximum_file_size_is_reached and self.__check_on_corruption(content=self.data):
                self.file_writer.submit_carved_file(content=self.data, file_extension=self.file_extension)
            return False
        return True

    def __check_on_corruption(self, content: bytes):
        if self.make_corruption_checks and self.corruption_check is not None:
            return self.corruption_check(content)
        return True
