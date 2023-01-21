from .abstract_worker import AbstractWorker


class WorkerSequenceTerminating(AbstractWorker):
    def __init__(self, file_extension: str, first_chunk: bytes, footer_sequence: bytes, maximal_size_in_bytes: int,
                 make_corruption_checks: bool, minimum_bytes=None, flush_if_maximum_file_size_is_reached=False,
                 corruption_check=None):
        super().__init__(first_chunk=first_chunk, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.footer_sequence = footer_sequence
        self.file_extension = file_extension
        self.maximal_size_in_bytes = maximal_size_in_bytes
        self.minimum_bytes = minimum_bytes
        self.corruption_check = corruption_check
        self.last_chunk = first_chunk

    def update(self, new_data_chunk: bytes) -> bool:
        """ returns True if object continues living otherwise False """

        last_two_chunks = self.last_chunk + new_data_chunk
        index_offset = len(self.data) - len(self.last_chunk)

        self.data += new_data_chunk
        self.last_chunk = new_data_chunk

        index_of_footer = last_two_chunks.find(self.footer_sequence)
        if index_of_footer > -1:
            end_index = index_offset + index_of_footer + len(self.footer_sequence)
            # store file
            if self.__check_on_corruption(content=self.data[:end_index]):
                self.file_writer.submit_carved_file(content=self.data[:end_index], file_extension=self.file_extension)
            return False
        else:
            if self.maximal_size_in_bytes is not None and len(self.data) > self.maximal_size_in_bytes:
                if self.flush_if_maximum_file_size_is_reached and self.__check_on_corruption(content=self.data):
                    self.file_writer.submit_carved_file(content=self.data, file_extension=self.file_extension)
                return False
        return True

    def __check_on_corruption(self, content: bytes):
        if self.make_corruption_checks and self.corruption_check is not None:
            return self.corruption_check(content)
        return True
