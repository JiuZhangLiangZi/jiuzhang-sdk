"""High-level local MNIST recognition task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.local.mnist.classifier import GBSMNISTClassifier
from jiuzhang.local.mnist.data import DatasetSource, load_mnist_data


@dataclass(frozen=True)
class GBSMNISTResult:
    """Result returned by ``run_mnist_recognition``."""

    train: dict[str, Any]
    accuracy: float
    predictions: npt.NDArray[np.int_]
    true_labels: npt.NDArray[np.int_]
    confusion_matrix: npt.NDArray[np.int_]
    source: str
    image_shape: tuple[int, int]

    def to_dict(self) -> dict[str, Any]:
        """Convert the result to JSON-friendly Python objects."""
        return {
            "train": self.train,
            "accuracy": self.accuracy,
            "predictions": self.predictions.tolist(),
            "true_labels": self.true_labels.tolist(),
            "confusion_matrix": self.confusion_matrix.tolist(),
            "source": self.source,
            "image_shape": list(self.image_shape),
        }


def run_mnist_recognition(
    *,
    train_size: int = 1200,
    test_size: int = 300,
    source: DatasetSource = "digits",
    n_components: int = 32,
    feature_count: int = 256,
    combine: bool = True,
    regularization: float = 1e-3,
    random_state: int = 7,
) -> GBSMNISTResult:
    """Run the complete local GBS handwritten digit recognition workflow.

    Args:
        train_size: Number of training samples used by the local task.
        test_size: Number of test samples used for evaluation.
        source: Dataset source. Use ``"digits"`` for fast offline demos and
            ``"openml"`` for the MNIST 784 dataset.
        n_components: PCA components retained before feature extraction.
        feature_count: Number of GBS-style features generated locally.
        combine: ``True`` uses GBS-RVFL, ``False`` uses GBS-ELM.
        regularization: Ridge regularization strength for the output layer.
        random_state: Seed for dataset shuffling and feature generation.

    Returns:
        A ``GBSMNISTResult`` object containing training metadata, accuracy,
        predictions, labels, and confusion matrix.
    """
    dataset = load_mnist_data(
        train_size=train_size,
        test_size=test_size,
        source=source,
        random_state=random_state,
    )
    classifier = GBSMNISTClassifier(
        n_components=n_components,
        feature_count=feature_count,
        regularization=regularization,
        random_state=random_state,
    )
    train = classifier.fit(dataset.train_data, dataset.train_labels, combine=combine)
    evaluation = classifier.evaluate(dataset.test_data, dataset.test_labels)
    return GBSMNISTResult(
        train=train,
        accuracy=float(evaluation["accuracy"]),
        predictions=np.asarray(evaluation["predictions"], dtype=np.int_),
        true_labels=np.asarray(evaluation["true_labels"], dtype=np.int_),
        confusion_matrix=np.asarray(evaluation["confusion_matrix"], dtype=np.int_),
        source=dataset.source,
        image_shape=dataset.image_shape,
    )
