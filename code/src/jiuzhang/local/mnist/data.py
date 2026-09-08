"""Dataset helpers for local handwritten digit recognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.mnist._deps import optional_dependency

DatasetSource = Literal["digits", "openml", "auto"]


@dataclass(frozen=True)
class HandwrittenDigitsData:
    """Train/test arrays used by the local recognition task."""

    train_data: npt.NDArray[np.float64]
    train_labels: npt.NDArray[np.int_]
    test_data: npt.NDArray[np.float64]
    test_labels: npt.NDArray[np.int_]
    source: str
    image_shape: tuple[int, int]


def load_mnist_data(
    *,
    train_size: int = 1200,
    test_size: int = 300,
    source: DatasetSource = "digits",
    random_state: int = 7,
) -> HandwrittenDigitsData:
    """Load handwritten digit data for the local GBS recognition demo.

    Args:
        train_size: Number of training samples returned to the caller.
        test_size: Number of test samples returned to the caller.
        source: Data source. ``"digits"`` uses the built-in scikit-learn
            handwritten digit dataset for fast offline demos. ``"openml"``
            downloads the full MNIST 784 dataset. ``"auto"`` tries OpenML and
            falls back to the built-in dataset.
        random_state: Seed used when shuffling samples before splitting.

    Returns:
        A ``HandwrittenDigitsData`` object containing feature arrays, labels,
        source name, and original image shape.
    """
    _validate_sizes(train_size=train_size, test_size=test_size)
    if source not in {"digits", "openml", "auto"}:
        raise InvalidParameterError("source must be 'digits', 'openml', or 'auto'")

    if source == "digits":
        return _load_digits(train_size, test_size, random_state=random_state)
    if source == "openml":
        return _load_openml_mnist(train_size, test_size, random_state=random_state)

    try:
        return _load_openml_mnist(train_size, test_size, random_state=random_state)
    except Exception:
        return _load_digits(train_size, test_size, random_state=random_state)


def _validate_sizes(*, train_size: int, test_size: int) -> None:
    if isinstance(train_size, bool) or not isinstance(train_size, int) or train_size <= 0:
        raise InvalidParameterError("train_size must be a positive integer")
    if isinstance(test_size, bool) or not isinstance(test_size, int) or test_size <= 0:
        raise InvalidParameterError("test_size must be a positive integer")


def _split_arrays(
    data: npt.NDArray[np.float64],
    labels: npt.NDArray[np.int_],
    *,
    train_size: int,
    test_size: int,
    random_state: int,
    source: str,
    image_shape: tuple[int, int],
) -> HandwrittenDigitsData:
    total = train_size + test_size
    if total > len(data):
        raise InvalidParameterError(
            f"train_size + test_size cannot exceed available sample count: {len(data)}"
        )

    rng = np.random.default_rng(random_state)
    indices = rng.permutation(len(data))[:total]
    selected_data = data[indices].astype(np.float64, copy=False)
    selected_labels = labels[indices].astype(np.int_, copy=False)
    scale = float(selected_data.max())
    if scale > 1.0:
        selected_data = selected_data / scale

    return HandwrittenDigitsData(
        train_data=selected_data[:train_size],
        train_labels=selected_labels[:train_size],
        test_data=selected_data[train_size:],
        test_labels=selected_labels[train_size:],
        source=source,
        image_shape=image_shape,
    )


def _load_digits(
    train_size: int,
    test_size: int,
    *,
    random_state: int,
) -> HandwrittenDigitsData:
    datasets = optional_dependency("sklearn.datasets", "scikit-learn")
    digits = datasets.load_digits()
    return _split_arrays(
        np.asarray(digits.data, dtype=np.float64),
        np.asarray(digits.target, dtype=np.int_),
        train_size=train_size,
        test_size=test_size,
        random_state=random_state,
        source="sklearn-digits",
        image_shape=(8, 8),
    )


def _load_openml_mnist(
    train_size: int,
    test_size: int,
    *,
    random_state: int,
) -> HandwrittenDigitsData:
    datasets = optional_dependency("sklearn.datasets", "scikit-learn")
    mnist = datasets.fetch_openml("mnist_784", version=1, as_frame=False, parser="auto")
    data = np.asarray(mnist.data, dtype=np.float64)
    labels = np.asarray(mnist.target, dtype=np.int_)
    return _split_arrays(
        data,
        labels,
        train_size=train_size,
        test_size=test_size,
        random_state=random_state,
        source="openml-mnist-784",
        image_shape=(28, 28),
    )
