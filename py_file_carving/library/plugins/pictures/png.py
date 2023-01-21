import io

from PIL import Image

from py_file_carving.library.worker import AbstractWorker, WorkerSequenceTerminating
from ..abstract_plugin import AbstractPlugin


class PNG(AbstractPlugin):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(file_writer=file_writer, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.pattern_trigger_sequence.append(bytes.fromhex('89504e470d0a1a0a0000000d49484452'))

    def create_worker(self, first_chunk: bytes) -> AbstractWorker:
        return WorkerSequenceTerminating(first_chunk=first_chunk,
                                         footer_sequence=bytes.fromhex('0000000049454e44ae426082'),
                                         maximal_size_in_bytes=5 * 1024 * 1024,
                                         file_extension='png',
                                         minimum_bytes=None,
                                         corruption_check=PNG.verify_png_is_not_corrupt,
                                         make_corruption_checks=self.make_corruption_checks)

    @staticmethod
    def verify_png_is_not_corrupt(binary_data: bytes) -> bool:
        try:
            im = Image.open(io.BytesIO(binary_data))
            im.verify()
            return True
        except IOError:
            return False
