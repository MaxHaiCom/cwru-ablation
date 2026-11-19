"""Fixed search ladder. One knob per rung. Batch size moves only on OOM."""

LR = (1e-3, 3e-4, 1e-4)
KERNEL = (8, 16, 32)
DILATION = (1, 2, 4)
BATCH = (32, 16, 8)
MAX_RUNGS = 6
KEYS = ("lr", "kernel", "dilation", "batch")


def baseline() -> dict[str, float | int]:
    return {"lr": LR[0], "kernel": KERNEL[0], "dilation": DILATION[0], "batch": BATCH[0]}


def _next_value(values: tuple[float, ...] | tuple[int, ...], current: float | int) -> float | int | None:
    index = values.index(current)  # type: ignore[arg-type]
    if index + 1 >= len(values):
        return None
    return values[index + 1]


def next_config(parent: dict[str, float | int], fuse: str | None, burned: set[tuple[str, float | int]]) -> dict[str, float | int] | None:
    proposal = dict(parent)
    if fuse == "oom":
        smaller = _next_value(BATCH, parent["batch"])
        if smaller is None:
            return None
        proposal["batch"] = smaller
    elif fuse == "nan":
        smaller = _next_value(LR, parent["lr"])
        if smaller is None:
            return None
        proposal["lr"] = smaller
    else:
        moved = False
        for key, values in (("lr", LR), ("kernel", KERNEL), ("dilation", DILATION)):
            nxt = _next_value(values, parent[key])
            if nxt is None:
                continue
            candidate = dict(parent)
            candidate[key] = nxt
            change = _only_change(parent, candidate)
            if change in burned:
                continue
            proposal = candidate
            moved = True
            break
        if not moved:
            return None
    change = _only_change(parent, proposal)
    if change is None or change in burned:
        return None
    return proposal


def _only_change(parent: dict[str, float | int], child: dict[str, float | int]) -> tuple[str, float | int] | None:
    changed = [key for key in KEYS if parent[key] != child[key]]
    if len(changed) != 1:
        return None
    key = changed[0]
    return key, child[key]


def legal(parent: dict[str, float | int], child: dict[str, float | int]) -> bool:
    return _only_change(parent, child) is not None
