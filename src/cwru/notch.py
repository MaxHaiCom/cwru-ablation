"""60 Hz notch at 12 kHz. Shaft frequency near 29 Hz must stay."""

import math

NOTCH_HZ = 60.0
SAMPLE_HZ = 12000.0
QUALITY = 30.0


def coefficients() -> tuple[float, float, float, float, float]:
    omega = 2 * math.pi * NOTCH_HZ / SAMPLE_HZ
    alpha = math.sin(omega) / (2 * QUALITY)
    cosine = math.cos(omega)
    b0, b1, b2 = 1.0, -2 * cosine, 1.0
    a0, a1, a2 = 1 + alpha, -2 * cosine, 1 - alpha
    return b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0


def apply_notch(samples: list[float]) -> list[float]:
    b0, b1, b2, a1, a2 = coefficients()
    x1 = x2 = y1 = y2 = 0.0
    output = []
    for sample in samples:
        filtered = b0 * sample + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, sample
        y2, y1 = y1, filtered
        output.append(filtered)
    return output
