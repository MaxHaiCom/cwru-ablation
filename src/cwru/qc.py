"""Drop a window whose peak-to-peak sits on the full-scale rails."""

WINDOW = 2048
HOP = 1024
FULL_SCALE_RATIO = 0.98


def windows(samples: list[float]) -> list[list[float]]:
    return [
        samples[start : start + WINDOW]
        for start in range(0, len(samples) - WINDOW + 1, HOP)
    ]


def is_clipped(window: list[float], full_scale: float) -> bool:
    if full_scale <= 0:
        raise ValueError("full_scale must be positive")
    peak_to_peak = max(window) - min(window)
    return peak_to_peak >= FULL_SCALE_RATIO * full_scale


def keep(samples: list[float], full_scale: float) -> list[list[float]]:
    return [window for window in windows(samples) if not is_clipped(window, full_scale)]
