import hashlib
import os
from multiprocessing import Queue
from queue import Empty
from threading import Thread, Lock

from cli_formatter.output_formatting import info


class FileWriter:
    def __init__(self, output_directory: str, no_equal_files: bool = True):
        self.carved_file_counter = dict()
        self.output_directory = output_directory
        self.queue = Queue()
        self.lock = Lock()
        self.is_running = False
        self.process = None

        self.no_equal_files = no_equal_files
        self.hashes_of_stored_files = dict()

    def submit_carved_file(self, content: bytes, file_extension: str) -> int or None:
        with self.lock:
            if not self.__check_if_file_should_be_stored(content=content, file_extension=file_extension):
                return None

            if file_extension not in self.carved_file_counter:
                self.carved_file_counter[file_extension] = 1
            else:
                self.carved_file_counter[file_extension] += 1
            filename = self.carved_file_counter[file_extension]
            self.queue.put((filename, file_extension, content))
            return filename

    def start(self):
        self.process = Thread(target=self.__run, daemon=True)
        self.is_running = True
        self.process.start()

    def stop(self):
        self.is_running = False
        self.process.join()

    def __run(self):
        while True:
            try:
                filename, file_extension, content = self.queue.get(block=True, timeout=0.5)
            except Empty:
                if not self.is_running:
                    break
            else:
                # store the carved file on the drive
                output_directory_for_file_type = os.path.join(self.output_directory, file_extension)
                if not os.path.exists(output_directory_for_file_type):
                    os.makedirs(output_directory_for_file_type)
                path_to_file = os.path.join(output_directory_for_file_type, '{}.{}'.format(filename, file_extension))
                with open(path_to_file, mode='wb') as carved_file:
                    carved_file.write(content)
                info('Carved new file: {}'.format(path_to_file))

    def __check_if_file_should_be_stored(self, content: bytes, file_extension: str) -> bool:
        if not self.no_equal_files:
            return True

        file_hash = FileWriter.__get_hash_from_file(content=content)

        if file_extension not in self.hashes_of_stored_files:
            self.hashes_of_stored_files[file_extension] = {file_hash}
            return True
        elif file_hash in self.hashes_of_stored_files[file_extension]:
            return False
        else:
            self.hashes_of_stored_files[file_extension].add(file_hash)
            return True

    @staticmethod
    def __get_hash_from_file(content: bytes) -> str:
        return hashlib.sha256(content).hexdigest()
