"""Antialias, then decimate 48 kHz to 12 kHz. No spline."""

import math

DECIMATE = 4
TAPS = 33
CUTOFF_HZ = 5000.0
SOURCE_HZ = 48000.0


def lowpass_taps() -> list[float]:
    cutoff = CUTOFF_HZ / SOURCE_HZ
    mid = (TAPS - 1) / 2
    taps = []
    for index in range(TAPS):
        offset = index - mid
        window = 0.54 - 0.46 * math.cos(2 * math.pi * index / (TAPS - 1))
        if offset == 0:
            sinc = 2 * cutoff
        else:
            sinc = math.sin(2 * math.pi * cutoff * offset) / (math.pi * offset)
        taps.append(sinc * window)
    scale = sum(taps)
    return [tap / scale for tap in taps]


def decimate_by_4(samples: list[float]) -> list[float]:
    taps = lowpass_taps()
    mid = (TAPS - 1) // 2
    output = []
    for start in range(0, len(samples) - TAPS + 1, DECIMATE):
        value = 0.0
        for index, tap in enumerate(taps):
            value += tap * samples[start + index]
        output.append(value)
    if mid:
        del output[: mid // DECIMATE]
    return output
