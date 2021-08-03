import argparse
import os
import time

from cli_formatter.output_formatting import warning, info

from .libary import FileCarver
from .libary.plugins import *


def __convert_seconds(seconds_total):
    hours = seconds_total // (60 * 60)
    minutes = (seconds_total - (hours * 60 * 60)) // 60
    seconds = seconds_total - (hours * 60 * 60) - (minutes * 60)
    return tuple([str(int(x)).rjust(2, '0') for x in [hours, minutes, seconds]])


def main():
    parser = argparse.ArgumentParser(usage='pyFileCarving -i INPUT -o OUTPUT')
    parser.add_argument('-i', '--input', type=str, help='Path to the device or file which should be scanned')
    parser.add_argument('-o', '--output', type=str, help='Path to the output directory')
    parser.add_argument('-c', '--no-corruption-checks', dest='no_corruption_checks', help='No corruption checks will be made, which faster the scan', action='store_true', default=False)
    parser.add_argument('-f', dest='flush_if_maximum_file_size_is_reached', help='Flush files when the maximum file size is reached even if its not completely carved', action='store_true', default=False)
    parser.add_argument('-p', '--plugin', type=str, nargs='+', dest='plugin_list', help='List of plugins which will be used [keys, cert, pictures, binary, pdf]', default=['keys', 'cert', 'pictures', 'binary', 'pdf'])

    arguments = parser.parse_args()

    if arguments.input is None:
        parser.print_help()
        exit()
    arguments.input = os.path.abspath(arguments.input)

    if arguments.output is None:
        parser.print_help()
        exit()
    arguments.output = os.path.abspath(arguments.output)

    file_carver = FileCarver(path_to_input_device=arguments.input,
                             output_directory=arguments.output,
                             make_corruption_checks=not arguments.no_corruption_checks,
                             flush_if_maximum_file_size_is_reached=arguments.flush_if_maximum_file_size_is_reached)

    # Private Keys
    if 'keys' in arguments.plugin_list:
        file_carver.register_plugin(EncryptedPrivateKey)
        file_carver.register_plugin(PrivateKey)
        file_carver.register_plugin(EncryptedPrivateKey)
        file_carver.register_plugin(PrivateDSAKey)
        file_carver.register_plugin(PrivateECKey)
        file_carver.register_plugin(PrivateRsaKey)

    # Certificates and Certificate Requests
    if 'cert' in arguments.plugin_list:
        file_carver.register_plugin(CertificateRequest)
        file_carver.register_plugin(Certificate)
        file_carver.register_plugin(TrustedCertificate)

    # Pictures
    if 'pictures' in arguments.plugin_list:
        file_carver.register_plugin(JPG)
        file_carver.register_plugin(PNG)

    # Binaries
    if 'binary' in arguments.plugin_list:
        file_carver.register_plugin(PeFile)

    # PDF
    if 'pdf' in arguments.plugin_list:
        file_carver.register_plugin(PDF)

    file_carver.start_scanning()

    try:
        time_started = time.time()
        info('Starting file carving process...')
        while file_carver.is_running:
            scanned_sectors = file_carver.scanned_sectors
            if scanned_sectors > 0:
                number_of_sectors = file_carver.number_of_sectors
                progress_in_percent = 100 * (scanned_sectors / number_of_sectors)
                # predict time it still takes
                duration_up_to_now = time.time() - time_started
                prediction_in_sec = (duration_up_to_now / scanned_sectors) * (number_of_sectors - scanned_sectors)
                d_hours, d_minutes, d_seconds = __convert_seconds(seconds_total=duration_up_to_now)
                p_hours, p_minutes, p_seconds = __convert_seconds(seconds_total=prediction_in_sec)
                info('{:2.2f}%    duration: {}:{}:{}  -  remaining: {}:{}:{}'.format(progress_in_percent, d_hours, d_minutes, d_seconds, p_hours, p_minutes, p_seconds))
            time.sleep(1)

        d_hours, d_minutes, d_seconds = __convert_seconds(time.time() - time_started)
        info('File carving process is complete. Needed: {}:{}:{}'.format(d_hours, d_minutes, d_seconds))

    except KeyboardInterrupt:
        warning('Keyboard Interrupt! Existing.')
        exit()


if __name__ == '__main__':
    main()
