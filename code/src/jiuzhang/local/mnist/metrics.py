"""Evaluation helpers for local recognition tasks."""

from __future__ import annotations

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError


def confusion_matrix(
    labels: npt.ArrayLike,
    predictions: npt.ArrayLike,
    *,
    n_classes: int = 10,
) -> npt.NDArray[np.int_]:
    """Build a confusion matrix from integer labels and predictions.

    Args:
        labels: True class labels.
        predictions: Predicted class labels.
        n_classes: Number of classes shown in the matrix.

    Returns:
        An ``n_classes x n_classes`` integer matrix. Rows represent true
        labels, and columns represent predicted labels.
    """
    if isinstance(n_classes, bool) or not isinstance(n_classes, int) or n_classes <= 0:
        raise InvalidParameterError("n_classes must be a positive integer")

    true_arr = np.asarray(labels, dtype=np.int_).reshape(-1)
    pred_arr = np.asarray(predictions, dtype=np.int_).reshape(-1)
    if true_arr.shape != pred_arr.shape:
        raise InvalidParameterError("labels and predictions must have the same length")

    matrix = np.zeros((n_classes, n_classes), dtype=np.int_)
    for true_value, pred_value in zip(true_arr, pred_arr, strict=True):
        if 0 <= true_value < n_classes and 0 <= pred_value < n_classes:
            matrix[int(true_value), int(pred_value)] += 1
    return matrix
