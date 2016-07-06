"""Module for splitting raw data into fixed-sized blocks."""

import numpy as np
import time


def _raw_reader(stream, chunk_size):
    """Read raw chunks of data."""
    while True:
        buf = stream.read(chunk_size)
        if len(buf) == 0:
            break
        yield buf


def _raw_block_reader(stream, block_size):
    """Read fixed-sized blocks of samples."""
    chunk = ""
    for raw in _raw_reader(stream, block_size - len(chunk)):
        if len(raw) == 0:
            chunk = raw
        else:
            chunk += raw

        if len(chunk) < block_size:
            continue

        data = np.frombuffer(chunk, dtype=np.uint8)

        yield data
        chunk = ""


def raw_to_complex(data):
    """Convert RTL-SDR I/Q interleaved samples to array of complex values.

    Parameters
    ----------
    data : :class:`numpy.ndarray` of `numpy.uint8`

    Returns
    -------
    :class:`numpy.ndarray` of `numpy.complex64`
    """
    values = data.astype(np.float32).view(np.complex64)
    values -= 127.4 + 127.4j
    values /= 128
    return values


def complex_to_raw(array):
    """Convert complex array back to I/Q interleaved RTL-SDR samples.

    Parameters
    ----------
    array : :class:`numpy.ndarray` of `numpy.complex64`

    Returns
    -------
    :class:`numpy.ndarray` of `numpy.uint8`
    """
    scaled = array.astype(np.complex64).view(np.float32) * 128 + 127.4
    return scaled.astype(np.uint8)


def block_reader(stream, size, history):
    """Read fixed-sized blocks from a stream of raw RTL-SDR samples.

    Parameters
    ----------
    stream : generator
        Raw 8-bit I/Q interleaved data from RTL-SDR.
    size : int
        Size of the blocks that should be generated.
    history : int
        Number of samples from the end of the previous block that should be
        included at the start of a new block.
        Each block will contain `size` - `history` new samples.

    Yields
    ------
    timestamp : float
        approximate time at which the data was captured
    block_idx : int
        block index, starting from zero for the first block
    data : :class:`numpy.ndarray`
        complex-valued array with the block's samples
    """
    new = size - history  # Number of new samples per block
    data = np.zeros(size)
    for block_idx, block in enumerate(_raw_block_reader(stream, new * 2)):
        new_data = raw_to_complex(block)
        data = np.concatenate([data[-history:], new_data])
        yield time.time(), block_idx, data