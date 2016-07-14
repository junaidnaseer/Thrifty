"""
Wrapper for using fastcard with a config file.

Example
-------
Assuming that all relevant settings are contained in the default config file,
blocks of data for which a carrier is detected can be captured from the RTL-SDR
using:

    $ fastcard_capture.py rx1.card


To check for detections without capturing it:

    $ fastcard_capture.py

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import subprocess
import sys
import logging

from thrifty import settings
from thrifty import setting_parsers


def _main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("output_file", nargs='?', help="Output file (.card)")
    parser.add_argument("--fastcard", dest="fastcard", default="fastcard",
                        help="Path to fastcard binary")
    setting_keys = ['sample_rate', 'tuner.freq', 'tuner.gain',
                    'block.size', 'block.history',
                    'carrier.window', 'carrier.threshold']
    config, args = settings.load_args(parser, setting_keys)

    bin_freq = config['sample_rate'] / config['block.size']
    window = setting_parsers.normalize_freq_range(
        config['carrier.window'], bin_freq)
    constant, snr, stddev = config['carrier.threshold']
    if stddev != 0:
        print("Warning: fastcard does not support 'stddev' in threshold "
              "formula", file=sys.stderr)

    call = [
        args['fastcard'],
        '-i', 'rtlsdr',
        '-s', str(config['sample_rate']),
        '-f', str(config['tuner.freq']),
        '-g', str(config['tuner.gain']),
        '-b', str(config['block.size']),
        '-h', str(config['block.history']),
        '-w', "{}-{}".format(window[0], window[1]),
        '-t', "{}c{}s".format(constant, snr)
    ]
    if args['output_file'] is not None:
        call.extend(['-o', args['output_file']])
    logging.info("Calling %s", ' '.join(call))
    returncode = subprocess.call(call)

    if returncode != 0:
        sys.exit(returncode)


if __name__ == '__main__':
    _main()