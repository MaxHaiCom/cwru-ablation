"""CWRU drive-end bearing, SKF 6205-2RS JEM geometry."""

BALL_COUNT = 9
BALL_DIAMETER_IN = 0.3126
PITCH_DIAMETER_IN = 1.537


def orders() -> dict[str, float]:
    ratio = BALL_DIAMETER_IN / PITCH_DIAMETER_IN
    return {
        "ftf": 0.5 * (1 - ratio),
        "bpfo": (BALL_COUNT / 2) * (1 - ratio),
        "bpfi": (BALL_COUNT / 2) * (1 + ratio),
        "bsf": (PITCH_DIAMETER_IN / (2 * BALL_DIAMETER_IN)) * (1 - ratio**2),
    }


def fault_hz(kind: str, rpm: float) -> float:
    return orders()[kind] * (rpm / 60.0)
