import logging
import re

import pefile
from bitarray import bitarray

from py_file_carving.libary.worker import AbstractWorker
from ..abstract_plugin import AbstractPlugin

logger = logging.getLogger(__name__)


class PeFile(AbstractPlugin):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(file_writer=file_writer, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.pattern_trigger_sequence.append(re.compile(bytes.fromhex('4d5a')))

    def create_worker(self, first_chunk: bytes) -> AbstractWorker:
        return PeFile_Worker(first_chunk=first_chunk, make_corruption_checks=self.make_corruption_checks,
                             flush_if_maximum_file_size_is_reached=self.flush_if_maximum_file_size_is_reached)


OFFSET_TO_POINTER_TO_PE_HEADER = 60


class PeFile_Worker(AbstractWorker):
    def __init__(self, first_chunk: bytes, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(first_chunk=first_chunk, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.data = first_chunk
        self.__storage = bitarray()

        self.__maximal_size_in_bytes = 232 * 1024 * 1024  # 232 MB
        self.__is_a_pe_file = False

    def update(self, new_data_chunk: bytes) -> bool:
        """ returns True if object continues living otherwise False """

        if not self.__is_a_pe_file:
            self.data += new_data_chunk

            if len(self.data) < 70:  # More data is needed
                return True
            else:
                pointer_to_pe_header_bytes = self.data[
                                             OFFSET_TO_POINTER_TO_PE_HEADER: OFFSET_TO_POINTER_TO_PE_HEADER + 1]
                pointer_to_pe_header = int.from_bytes(pointer_to_pe_header_bytes, byteorder='big')

                if len(self.data) < pointer_to_pe_header + 2:  # More data is needed
                    return True

                if self.data[pointer_to_pe_header: pointer_to_pe_header + 2] == b'PE':
                    self.__storage.frombytes(self.data)
                    self.__is_a_pe_file = True
                else:
                    return False
        else:
            new_data = bitarray()
            new_data.frombytes(new_data_chunk)
            self.__storage.extend(new_data)

        if len(self.__storage) / 8 >= self.__maximal_size_in_bytes or len(new_data_chunk) == 0:
            self.data = self.__storage.tobytes()

            try:
                parsed_pe_file = pefile.PE(data=self.data)
            except pefile.PEFormatError as exception:
                logger.critical('PE-File could not be parsed: {}'.format(exception))
                return False  # len(self.data) <= self.__maximal_size_in_bytes           # maybe still some data is missing
            else:
                file_extension = PeFile_Worker.__determine_file_extension(parsed_pe_file=parsed_pe_file)

                # calculate the size of the complete PE-File - this enables the determination of the EOF
                size = parsed_pe_file.NT_HEADERS.OPTIONAL_HEADER.SizeOfHeaders
                for s in parsed_pe_file.sections:
                    size += s.SizeOfRawData

                carved_file = self.data[:size]

                self.file_writer.submit_carved_file(content=carved_file, file_extension=file_extension)
                return False
        else:
            return True

    @staticmethod
    def __determine_file_extension(parsed_pe_file: pefile.PE) -> str:
        if parsed_pe_file.is_dll():
            return 'dll'
        if parsed_pe_file.is_driver():
            return 'sys'
        if parsed_pe_file.is_exe():
            return 'exe'
        else:
            return 'bin'
