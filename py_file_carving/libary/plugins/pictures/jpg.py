import io
import logging
import re

from PIL import Image

from py_file_carving.libary.worker import AbstractWorker
from ..abstract_plugin import AbstractPlugin

logger = logging.getLogger(__name__)


class JPG(AbstractPlugin):
    def __init__(self, file_writer, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(file_writer=file_writer, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.pattern_trigger_sequence.append(re.compile(rb'\xff\xd8\xff\xe1'))
        self.pattern_trigger_sequence.append(re.compile(rb'\xff\xd8\xff\xdb'))
        self.pattern_trigger_sequence.append(re.compile(rb'\xff\xd8\xff\xe0\x00\x10\x4a\x46\x49\x46\x00\x01'))
        self.pattern_trigger_sequence.append(re.compile(rb'\xff\xd8\xff\xee'))

    def create_worker(self, first_chunk: bytes) -> AbstractWorker:
        return JPG_Worker(first_chunk=first_chunk, make_corruption_checks=self.make_corruption_checks,
                          flush_if_maximum_file_size_is_reached=self.flush_if_maximum_file_size_is_reached)


class JPG_Worker(AbstractWorker):
    def __init__(self, first_chunk: bytes, make_corruption_checks: bool, flush_if_maximum_file_size_is_reached: bool):
        super().__init__(first_chunk=first_chunk, make_corruption_checks=make_corruption_checks,
                         flush_if_maximum_file_size_is_reached=flush_if_maximum_file_size_is_reached)
        self.__maximal_size_in_bytes = 8 * 1024 * 1024
        self.__last_chunk = first_chunk

        self.markers_to_ignore = set()
        self.markers_to_ignore.add(b'\xd0')
        self.markers_to_ignore.add(b'\xd1')
        self.markers_to_ignore.add(b'\xd2')
        self.markers_to_ignore.add(b'\xd3')
        self.markers_to_ignore.add(b'\xd4')
        self.markers_to_ignore.add(b'\xd5')
        self.markers_to_ignore.add(b'\xd6')
        self.markers_to_ignore.add(b'\xd7')
        self.markers_to_ignore.add(b'\xd8')
        self.markers_to_ignore.add(b'\xd9')
        self.markers_to_ignore.add(b'\x01')
        self.markers_to_ignore.add(b'\x00')
        self.markers_to_ignore.add(b'\xff')

        self.last_marker_position = 0

    def update(self, new_data_chunk: bytes) -> bool:
        """ returns True if object continues living otherwise False """
        self.data += new_data_chunk

        search_data = self.__last_chunk + new_data_chunk
        index_offset = len(self.data) - len(self.__last_chunk) - len(new_data_chunk)

        for m in re.finditer(re.compile(rb'\xff'), search_data):
            marker_start = m.start(0)
            marker_end = marker_start + 2

            if index_offset + marker_start < self.last_marker_position:  # this is not a marker - the \xff\xXX is contained in an other segment
                continue

            marker_identifier = search_data[marker_start + 1:marker_end]
            if marker_identifier in self.markers_to_ignore:  # this is not a marker
                continue

            length_field_index_start = marker_end
            length_field_index_end = marker_end + 2
            length_in_bytes = search_data[length_field_index_start:length_field_index_end]
            if len(length_in_bytes) < 2:  # break since not enough data is read yet
                break

            length_of_segment = int.from_bytes(length_in_bytes, byteorder='big')
            self.last_marker_position += length_of_segment - 2

        for footer_match in re.finditer(re.compile(rb'\xff\xd9'), search_data):
            footer_end = index_offset + footer_match.end(0)

            if footer_end < self.last_marker_position:  # footer is part of an embedded file
                continue

            image_data = self.data[:footer_end]

            # store the image only if its not corrupt
            if JPG_Worker.__is_not_corrupt(binary_data=image_data):
                self.file_writer.submit_carved_file(content=image_data, file_extension='jpg')

            return False

        if len(self.data) > self.__maximal_size_in_bytes:
            return False

        self.__last_chunk = new_data_chunk
        return True

    @staticmethod
    def __is_not_corrupt(binary_data: bytes) -> bool:
        try:
            im = Image.open(io.BytesIO(binary_data))
            im.verify()
            return True
        except IOError:
            return False
