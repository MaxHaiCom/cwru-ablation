"""Lock the split, the seed, and the scoring function. No dataset and no training."""

import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from cwru.ladder import baseline, legal, next_config  # noqa: E402
from cwru.metrics import cell_passed, rung_accepted  # noqa: E402
from cwru.notch import apply_notch  # noqa: E402
from cwru.orders import fault_hz, orders  # noqa: E402
from cwru.qc import is_clipped  # noqa: E402
from cwru.resample import decimate_by_4  # noqa: E402

LOCKS = Path(__file__).with_name("locks.json")
SPLIT_DIR = ROOT / "splits"
CELL_DIR = ROOT / "configs" / "cells"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_flat(text: str) -> dict[str, object]:
    parsed: dict[str, object] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        key, raw_value = line.split(":", 1)
        value = raw_value.strip()
        if value.replace(".", "", 1).isdigit():
            parsed[key.strip()] = float(value) if "." in value else int(value)
        else:
            parsed[key.strip()] = value
    return parsed


def fail(message: str) -> None:
    print(f"check {message}")
    raise SystemExit(1)


def sine(hz: float, sample_hz: float, seconds: float) -> list[float]:
    count = int(sample_hz * seconds)
    return [math.sin(2 * math.pi * hz * index / sample_hz) for index in range(count)]


def rms(samples: list[float]) -> float:
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


def check_locks() -> None:
    current = {
        "metrics": sha256(ROOT / "src" / "cwru" / "metrics.py"),
        "ladder": sha256(ROOT / "src" / "cwru" / "ladder.py"),
        "splits": {
            path.name: sha256(path) for path in sorted(SPLIT_DIR.glob("load*.json"))
        },
    }
    locked = json.loads(LOCKS.read_text())
    if current != locked:
        fail("split, ladder, or metric hash changed")


def check_splits() -> None:
    files = json.loads((ROOT / "data" / "files.json").read_text())["records"]
    by_load: dict[int, list[int]] = {0: [], 1: [], 2: [], 3: []}
    for record in files:
        by_load[record["load_hp"]].append(record["file"])
    for load, expected_test in by_load.items():
        split = json.loads((SPLIT_DIR / f"load{load}.json").read_text())
        if split["seed"] != 7 or split["load_hp"] != load:
            fail(f"load{load} seed or load")
        if split["test_files"] != expected_test:
            fail(f"load{load} test files")
        overlap = set(split["test_files"]) & set(split["train_files"])
        if overlap or sorted(split["train_files"]) == sorted(expected_test):
            fail(f"load{load} train leaks into test")


def check_cells() -> None:
    required = {
        "seed": 7,
        "sample_rate_hz": 12000,
        "window": 2048,
        "hop": 1024,
        "fault_diameter_in": 0.007,
        "target_macro_f1": 0.85,
        "max_normal_fpr_at_recall_0_90": 0.10,
    }
    names = sorted(path.stem for path in CELL_DIR.glob("*.yaml"))
    expected = [
        f"load{load}_{model}"
        for load in range(4)
        for model in ("cnn1d", "envelope_lr")
    ]
    if names != expected:
        fail("cell matrix")
    for path in sorted(CELL_DIR.glob("*.yaml")):
        cell = parse_flat(path.read_text())
        for key, value in required.items():
            if cell.get(key) != value:
                fail(f"{path.name} {key}")
        if cell["model"] == "cnn1d":
            parent = baseline()
            if any(cell.get(key) != value for key, value in parent.items()):
                fail(f"{path.name} is not the frozen baseline")
            if cell.get("optimizer") != "adamw" or cell.get("loss") != "cross_entropy":
                fail(f"{path.name} optimizer or loss")
            if cell.get("grad_clip") != 1.0:
                fail(f"{path.name} grad clip")


def check_signal() -> None:
    low = rms(decimate_by_4(sine(1000, 48000, 0.05))[20:])
    high = rms(decimate_by_4(sine(10000, 48000, 0.05))[20:])
    if low <= high * 5:
        fail("decimator did not reject 10 kHz")
    tone_60 = rms(apply_notch(sine(60, 12000, 0.5))[2000:])
    tone_29 = rms(apply_notch(sine(29, 12000, 0.5))[2000:])
    if tone_29 <= tone_60 * 5:
        fail("notch hit the shaft tone or missed 60 Hz")
    if not is_clipped([-1.0, 1.0], 2.0):
        fail("clip rule")
    bpfo = fault_hz("bpfo", 1730)
    if not 100 < bpfo < 110:
        fail(f"load 3 outer-race frequency {bpfo}")
    if orders()["bpfo"] < 3.5:
        fail("bearing order")


def check_ladder() -> None:
    parent = baseline()
    first = next_config(parent, None, set())
    if first is None or not legal(parent, first) or first["lr"] != 3e-4:
        fail("first rung must lower lr only")
    oom = next_config(parent, "oom", set())
    if oom is None or oom["batch"] != 16:
        fail("oom fuse")
    stuck = dict(parent)
    stuck["batch"] = 8
    if next_config(stuck, "oom", set()) is not None:
        fail("batch 8 oom must stop")
    nan = next_config(parent, "nan", set())
    if nan is None or nan["lr"] != 3e-4:
        fail("nan fuse")
    if legal(parent, {"lr": 1e-4, "kernel": 32, "dilation": 4, "batch": 8}):
        fail("two-knob edit must be illegal")
    before = {"macro_f1": 0.70, "inner": 0.80, "outer": 0.75, "ball": 0.40}
    if rung_accepted(before, {"macro_f1": 0.705, "inner": 0.80, "outer": 0.75, "ball": 0.90}):
        fail("tiny gain must be rejected")
    if rung_accepted(before, {"macro_f1": 0.80, "inner": 0.70, "outer": 0.75, "ball": 0.90}):
        fail("class drop must be rejected")
    if not rung_accepted(before, {"macro_f1": 0.76, "inner": 0.80, "outer": 0.75, "ball": 0.55}):
        fail("clean gain must be kept")
    if cell_passed(0.84, 0.01) or not cell_passed(0.85, 0.10):
        fail("cell bar")


def main() -> None:
    check_locks()
    check_splits()
    check_cells()
    check_signal()
    check_ladder()
    print("check ok")


if __name__ == "__main__":
    main()
