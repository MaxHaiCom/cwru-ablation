"""Scoring function. harness/check.py hashes this file. Do not edit it to pass a cell."""

CLASSES = ("normal", "inner", "outer", "ball")
TARGET_MACRO_F1 = 0.85
NORMAL_RECALL = 0.90
MAX_NORMAL_FPR = 0.10
MIN_MACRO_F1_GAIN = 0.01
MAX_OTHER_F1_DROP = 0.05


def class_f1(true_labels: list[str], pred_labels: list[str], label: str) -> float:
    if len(true_labels) != len(pred_labels) or not true_labels:
        raise ValueError("label vectors must be the same non-empty length")
    tp = fp = fn = 0
    for truth, pred in zip(true_labels, pred_labels):
        if pred == label and truth == label:
            tp += 1
        elif pred == label:
            fp += 1
        elif truth == label:
            fn += 1
    if tp == 0:
        return 0.0
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    return 2 * precision * recall / (precision + recall)


def macro_f1(true_labels: list[str], pred_labels: list[str]) -> float:
    scores = [class_f1(true_labels, pred_labels, label) for label in CLASSES]
    return sum(scores) / len(CLASSES)


def normal_fpr_at_recall(scores: list[float], labels: list[str]) -> float:
    """scores are P(normal). Threshold is set at the requested normal recall."""
    normal_scores = sorted(score for score, label in zip(scores, labels) if label == "normal")
    if not normal_scores:
        raise ValueError("recall point needs normal examples")
    keep_count = max(1, int(round(NORMAL_RECALL * len(normal_scores))))
    threshold = normal_scores[-keep_count]
    negatives = [score for score, label in zip(scores, labels) if label != "normal"]
    if not negatives:
        raise ValueError("false-alarm rate needs non-normal examples")
    false_alarms = sum(score >= threshold for score in negatives)
    return false_alarms / len(negatives)


def cell_passed(macro: float, normal_fpr: float) -> bool:
    return macro >= TARGET_MACRO_F1 and normal_fpr <= MAX_NORMAL_FPR


def rung_accepted(before: dict[str, float], after: dict[str, float]) -> bool:
    if after["macro_f1"] < before["macro_f1"] + MIN_MACRO_F1_GAIN:
        return False
    for label in ("inner", "outer", "ball"):
        if after[label] < before[label] - MAX_OTHER_F1_DROP:
            return False
    return True
