from multiprocessing import Queue
from queue import Empty
from threading import Thread
from typing import Type

import parted
from cli_formatter.output_formatting import error, info

from .file_writer import FileWriter
from .plugins.abstract_plugin import AbstractPlugin


class FileCarver:
    def __init__(self, path_to_input_device: str, output_directory: str, flush_if_maximum_file_size_is_reached: bool,
                 make_corruption_checks: bool = False, no_equal_files: bool = True, buffer_size: int = 50):
        self.file_writer = FileWriter(output_directory=output_directory, no_equal_files=no_equal_files)
        self.buffer = Queue(maxsize=buffer_size)
        self.path_to_input_device = path_to_input_device
        self.scanned_sectors = 0
        self.number_of_sectors = 0
        self.is_running = False
        self.make_corruption_checks = make_corruption_checks
        self.flush_if_maximum_file_size_is_reached = flush_if_maximum_file_size_is_reached
        self.plugin_list = list()
        self.worker_list = list()

    def register_plugin(self, plugin: Type[AbstractPlugin]):
        self.plugin_list.append(plugin(file_writer=self.file_writer, make_corruption_checks=self.make_corruption_checks,
                                       flush_if_maximum_file_size_is_reached=self.flush_if_maximum_file_size_is_reached))

    def submit_new_input_data(self, data):
        self.buffer.put(data, block=True)

    def start_scanning(self):
        try:
            device = parted.getDevice(self.path_to_input_device)
        except Exception as exception:
            error('Input Device could not be read: {}'.format(exception))
            self.is_running = False
            exit()
        else:
            self.is_running = True
            t = Thread(target=self.__start_scanning, args=(device, ), daemon=True)
            t.start()

    def __start_scanning(self, device):
        self.scanned_sectors = 0

        self.file_writer.start()

        reader_thread = Thread(target=self.__read_data, args=(device, ), daemon=True)
        reader_thread.start()

        self.__scan_data()

        reader_thread.join()
        self.file_writer.stop()

        self.is_running = False

    def __read_data(self, device):
        self.number_of_sectors = device.length
        self.size_of_a_sector = device.sectorSize
        info('Model of input device: {}'.format(device.model))
        info('Number of sectors: {}'.format(self.number_of_sectors))
        info('Bytes per sector: {}'.format(self.size_of_a_sector))

        try:
            with open(self.path_to_input_device, mode='rb') as input_file:
                input_file.seek(0)
                for sector_i in range(self.number_of_sectors + 1):
                    data_of_new_sector = input_file.read(self.size_of_a_sector)
                    self.buffer.put(data_of_new_sector, block=True)
        except IsADirectoryError:
            error('The Input has to be a drive not an directory')
            self.is_running = False
            exit()

    def __scan_data(self):
        info('start file carving...')
        sector_before = bytes()
        self.scanned_sectors = 0
        self.worker_list = list()
        while True:
            try:
                next_sector = self.buffer.get(block=True, timeout=0.01)

                # update current worker
                workers_to_remove = list()
                for worker in self.worker_list:
                    maintain_worker = worker.update(next_sector)
                    if not maintain_worker:
                        workers_to_remove.append(worker)

                # remove workers which which should no longer be maintained
                for worker in workers_to_remove:
                    self.worker_list.remove(worker)

                # check for new start triggers
                search_bytes = sector_before + next_sector
                index_offset = max((self.scanned_sectors - 1), 0) * self.size_of_a_sector
                for plugin in self.plugin_list:
                    new_workers = plugin.check_for_trigger_sequence(index_offset=index_offset, search_data=search_bytes)
                    self.worker_list.extend(new_workers)

                sector_before = next_sector
                self.scanned_sectors += 1

            except Empty:
                if self.scanned_sectors >= self.number_of_sectors != 0:
                    for worker in self.worker_list:
                        worker.end_of_data_signal()
                    info('Complete Input was processed')
                    break
