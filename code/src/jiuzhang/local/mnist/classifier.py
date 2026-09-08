"""Local GBS-style classifier for handwritten digit recognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
import numpy.typing as npt

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.mnist._deps import optional_dependency
from jiuzhang.local.mnist.metrics import confusion_matrix


@dataclass(frozen=True)
class _PreparedTargets:
    labels: npt.NDArray[np.int_]
    one_hot: npt.NDArray[np.float64]


class GBSMNISTClassifier:
    """Local classifier used by the SDK MNIST recognition demo.

    The classifier follows the same user-facing workflow as the original
    GBS-RVFL / GBS-ELM notebook: PCA dimension reduction, a GBS-style nonlinear
    feature layer, optional concatenation with original input features, and a
    closed-form output layer.
    """

    def __init__(
        self,
        *,
        n_components: int = 32,
        feature_count: int = 256,
        regularization: float = 1e-3,
        random_state: int = 7,
    ) -> None:
        """Initialize the local classifier.

        Args:
            n_components: PCA components retained before feature extraction.
            feature_count: Number of generated GBS-style features.
            regularization: Ridge regularization strength for the output layer.
            random_state: Seed used by PCA and deterministic feature projection.
        """
        self.n_components = _positive_int(n_components, name="n_components")
        self.feature_count = _positive_int(feature_count, name="feature_count")
        self.regularization = _non_negative_float(regularization, name="regularization")
        self.random_state = int(random_state)

        decomposition = optional_dependency("sklearn.decomposition", "scikit-learn")
        self._pca: Any = decomposition.PCA(
            n_components=self.n_components,
            random_state=self.random_state,
        )
        self._projection: npt.NDArray[np.float64] | None = None
        self._bias: npt.NDArray[np.float64] | None = None
        self._weights: npt.NDArray[np.float64] | None = None
        self._combine = True
        self._last_train_gbs_features: npt.NDArray[np.float64] | None = None
        self._last_test_gbs_features: npt.NDArray[np.float64] | None = None

    def fit(
        self,
        data: npt.ArrayLike,
        targets: npt.ArrayLike,
        *,
        combine: bool = True,
        feature_count: int | None = None,
        reuse: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Train the classifier.

        Args:
            data: Training samples. Each row is one flattened digit image.
            targets: Either integer labels or a one-hot target matrix.
            combine: ``True`` selects the GBS-RVFL mode by concatenating local
                GBS features with original pixels. ``False`` selects GBS-ELM.
            feature_count: Number of GBS-style features used by this fit.
            reuse: Reuse cached train features from the previous fit.
            **kwargs: Supports ``IndexNumber`` as a compatibility alias for
                the original notebook.

        Returns:
            Training metadata including mode, feature count, and PCA variance.
        """
        train = _samples(data)
        prepared = _prepare_targets(targets)
        if train.shape[0] != prepared.one_hot.shape[0]:
            raise InvalidParameterError("data and targets must have the same row count")
        if self.n_components > min(train.shape):
            raise InvalidParameterError("n_components cannot exceed min(data.shape)")

        legacy_index_number = kwargs.pop("IndexNumber", None)
        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise InvalidParameterError(f"unsupported fit parameter(s): {names}")

        requested_features = _resolve_feature_count(
            feature_count,
            legacy_index_number,
            self.feature_count,
        )
        self.feature_count = requested_features
        self._combine = bool(combine)

        if (
            reuse
            and self._last_train_gbs_features is not None
            and self._last_train_gbs_features.shape == (train.shape[0], self.feature_count)
        ):
            gbs_features = self._last_train_gbs_features
        else:
            reduced = np.asarray(self._pca.fit_transform(train), dtype=np.float64)
            gbs_features = self._extract_features(reduced)
            self._last_train_gbs_features = gbs_features
            self._last_test_gbs_features = None
        feature_matrix = _combine_features(gbs_features, train, combine=self._combine)

        self._weights = _solve_output_weights(
            feature_matrix,
            prepared.one_hot,
            regularization=self.regularization,
        )
        variance = float(np.sum(np.asarray(self._pca.explained_variance_ratio_, dtype=np.float64)))
        return {
            "status": "trained",
            "mode": "GBS-RVFL" if self._combine else "GBS-ELM",
            "n_components": self.n_components,
            "feature_count": self.feature_count,
            "pca_explained_variance_ratio": variance,
        }

    def predict(self, data: npt.ArrayLike, *, reuse: bool = False) -> npt.NDArray[np.int_]:
        """Predict integer digit labels.

        Args:
            data: Test samples. Each row is one flattened digit image.
            reuse: Reuse cached test features from the previous prediction.

        Returns:
            Predicted class labels.
        """
        if self._weights is None:
            raise InvalidParameterError("classifier must be fitted before predict()")

        test = _samples(data)
        if (
            reuse
            and self._last_test_gbs_features is not None
            and self._last_test_gbs_features.shape == (test.shape[0], self.feature_count)
        ):
            gbs_features = self._last_test_gbs_features
        else:
            reduced = np.asarray(self._pca.transform(test), dtype=np.float64)
            gbs_features = self._extract_features(reduced)
            self._last_test_gbs_features = gbs_features
        feature_matrix = _combine_features(gbs_features, test, combine=self._combine)

        scores = feature_matrix @ self._weights
        predictions: npt.NDArray[np.int_] = np.asarray(np.argmax(scores, axis=1), dtype=np.int_)
        return predictions

    def evaluate(
        self,
        data: npt.ArrayLike,
        labels: npt.ArrayLike,
        *,
        reuse: bool = False,
    ) -> dict[str, Any]:
        """Evaluate the classifier on labeled data.

        Args:
            data: Test samples.
            labels: True integer labels.
            reuse: Reuse cached test features from the previous prediction.

        Returns:
            Accuracy, predictions, true labels, and confusion matrix.
        """
        true_labels = np.asarray(labels, dtype=np.int_).reshape(-1)
        predictions = self.predict(data, reuse=reuse)
        if predictions.shape != true_labels.shape:
            raise InvalidParameterError("data and labels must have the same row count")
        accuracy = float(np.mean(predictions == true_labels))
        return {
            "accuracy": accuracy,
            "predictions": predictions,
            "true_labels": true_labels,
            "confusion_matrix": confusion_matrix(true_labels, predictions),
        }

    def _extract_features(self, reduced: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        if self._projection is None or self._projection.shape != (
            reduced.shape[1],
            self.feature_count,
        ):
            rng = np.random.default_rng(self.random_state)
            scale = 1.0 / np.sqrt(max(reduced.shape[1], 1))
            self._projection = rng.normal(0.0, scale, size=(reduced.shape[1], self.feature_count))
            self._bias = rng.uniform(0.0, np.pi, size=self.feature_count)

        if self._bias is None:
            raise InvalidParameterError("feature projection is not initialized")
        activated = reduced @ self._projection + self._bias
        features: npt.NDArray[np.float64] = np.asarray(
            np.square(np.cos(activated)),
            dtype=np.float64,
        )
        return features


def _positive_int(value: Any, *, name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise InvalidParameterError(f"{name} must be a positive integer")
    return value


def _non_negative_float(value: Any, *, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise InvalidParameterError(f"{name} must be non-negative")
    result = float(value)
    if result < 0:
        raise InvalidParameterError(f"{name} must be non-negative")
    return result


def _resolve_feature_count(
    feature_count: int | None,
    legacy_index_number: int | None,
    default: int,
) -> int:
    if feature_count is not None and legacy_index_number is not None:
        raise InvalidParameterError("feature_count and IndexNumber cannot be set at the same time")
    value = feature_count if feature_count is not None else legacy_index_number
    return _positive_int(value if value is not None else default, name="feature_count")


def _samples(data: npt.ArrayLike) -> npt.NDArray[np.float64]:
    arr = np.asarray(data, dtype=np.float64)
    if arr.ndim != 2 or arr.shape[0] == 0 or arr.shape[1] == 0:
        raise InvalidParameterError("data must be a non-empty 2D array")
    return arr


def _prepare_targets(targets: npt.ArrayLike) -> _PreparedTargets:
    arr = np.asarray(targets)
    if arr.ndim == 1:
        labels = arr.astype(np.int_, copy=False)
        n_classes = int(labels.max()) + 1
        one_hot = np.eye(n_classes, dtype=np.float64)[labels]
        return _PreparedTargets(labels=labels, one_hot=one_hot)
    if arr.ndim == 2 and arr.shape[0] > 0 and arr.shape[1] > 0:
        labels = np.argmax(arr, axis=1).astype(np.int_)
        return _PreparedTargets(labels=labels, one_hot=arr.astype(np.float64, copy=False))
    raise InvalidParameterError("targets must be labels or a one-hot matrix")


def _combine_features(
    gbs_features: npt.NDArray[np.float64],
    raw_data: npt.NDArray[np.float64],
    *,
    combine: bool,
) -> npt.NDArray[np.float64]:
    if not combine:
        return gbs_features
    return np.concatenate([gbs_features, raw_data], axis=1)


def _solve_output_weights(
    features: npt.NDArray[np.float64],
    targets: npt.NDArray[np.float64],
    *,
    regularization: float,
) -> npt.NDArray[np.float64]:
    lhs = features.T @ features
    if regularization > 0:
        lhs = lhs + np.eye(lhs.shape[0], dtype=np.float64) * regularization
    rhs = features.T @ targets
    return np.linalg.solve(lhs, rhs)
