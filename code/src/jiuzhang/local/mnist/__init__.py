"""Local handwritten digit recognition helpers."""

from __future__ import annotations

from jiuzhang.local.mnist.classifier import GBSMNISTClassifier
from jiuzhang.local.mnist.data import HandwrittenDigitsData, load_mnist_data
from jiuzhang.local.mnist.metrics import confusion_matrix
from jiuzhang.local.mnist.task import GBSMNISTResult, run_mnist_recognition

GBSClassifier = GBSMNISTClassifier

__all__ = [
    "GBSClassifier",
    "GBSMNISTClassifier",
    "GBSMNISTResult",
    "HandwrittenDigitsData",
    "confusion_matrix",
    "load_mnist_data",
    "run_mnist_recognition",
]
