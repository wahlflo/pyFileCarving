import io
import logging
import re

import PyPDF2
import PyPDF2.utils

from py_file_carving.libary.worker import WorkerMaximalSizeTerminating
from ..abstract_plugin import AbstractPlugin

logger = logging.getLogger(__name__)


class PDF(AbstractPlugin):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(file_writer=file_writer, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.pattern_trigger_sequence.append(re.compile(b'%PDF-'))

    def create_worker(self, first_chunk: bytes):
        return WorkerMaximalSizeTerminating(first_chunk=first_chunk,
                                            footer_sequence=b'%EOF\r\n',
                                            maximal_size_in_bytes=8 * 1024 * 1024,
                                            file_extension='pdf',
                                            corruption_check=PDF.__is_not_corrupt,
                                            make_corruption_checks=self.make_corruption_checks)

    @staticmethod
    def __is_not_corrupt(binary_data: bytes) -> bool:
        try:
            PyPDF2.PdfFileReader(io.BytesIO(binary_data))
            return True
        except PyPDF2.utils.PdfReadError:
            return False
