"""Run one cell. Refuses to start when the lock check fails or the mat files are absent."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    if len(sys.argv) != 2:
        print("usage: python3 harness/run_cell.py configs/cells/<cell>.yaml")
        raise SystemExit(2)
    cell = Path(sys.argv[1])
    if not cell.is_file():
        print(f"missing {cell}")
        raise SystemExit(2)
    lock = subprocess.run([sys.executable, str(ROOT / "harness" / "check.py")], check=False)
    if lock.returncode != 0:
        raise SystemExit(lock.returncode)
    manifest = ROOT / "data" / "manifest.json"
    if not manifest.is_file():
        print("data/manifest.json is missing. Download the mat files, hash them, and do not commit the mat files.")
        raise SystemExit(2)
    print(f"locked. cell {cell.name} is ready for one run. Training stays outside this check.")


if __name__ == "__main__":
    main()
