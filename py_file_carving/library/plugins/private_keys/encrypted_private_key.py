import re

from py_file_carving.library.plugins.abstract_plugin import AbstractPlugin
from py_file_carving.library.worker import WorkerSequenceTerminating


class EncryptedPrivateKey(AbstractPlugin):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(file_writer=file_writer, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.pattern_trigger_sequence.append(re.compile(b'-----BEGIN ENCRYPTED PRIVATE KEY-----'))

    def create_worker(self, first_chunk: bytes):
        return WorkerSequenceTerminating(first_chunk=first_chunk,
                                         footer_sequence=b'-----END ENCRYPTED PRIVATE KEY-----',
                                         maximal_size_in_bytes=50 * 1024,
                                         file_extension='private_key',
                                         make_corruption_checks=self.make_corruption_checks)
