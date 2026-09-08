from __future__ import annotations

import numpy as np
import pytest

from jiuzhang.exceptions import InvalidParameterError
from jiuzhang.local.mnist import (
    GBSMNISTClassifier,
    confusion_matrix,
    load_mnist_data,
    run_mnist_recognition,
)

pytest.importorskip("sklearn")


def test_load_mnist_data_returns_train_and_test_arrays() -> None:
    dataset = load_mnist_data(train_size=40, test_size=10, source="digits", random_state=1)

    assert dataset.train_data.shape == (40, 64)
    assert dataset.test_data.shape == (10, 64)
    assert dataset.train_labels.shape == (40,)
    assert dataset.test_labels.shape == (10,)
    assert dataset.source == "sklearn-digits"
    assert dataset.image_shape == (8, 8)
    assert float(dataset.train_data.min()) >= 0.0
    assert float(dataset.train_data.max()) <= 1.0


def test_gbs_mnist_classifier_fit_predict_evaluate() -> None:
    dataset = load_mnist_data(train_size=80, test_size=20, source="digits", random_state=2)
    classifier = GBSMNISTClassifier(
        n_components=8,
        feature_count=24,
        regularization=1e-2,
        random_state=2,
    )

    train = classifier.fit(dataset.train_data, dataset.train_labels, combine=True)
    predictions = classifier.predict(dataset.test_data)
    evaluation = classifier.evaluate(dataset.test_data, dataset.test_labels, reuse=True)

    assert train["status"] == "trained"
    assert train["mode"] == "GBS-RVFL"
    assert train["feature_count"] == 24
    assert predictions.shape == (20,)
    assert 0.0 <= evaluation["accuracy"] <= 1.0
    assert np.asarray(evaluation["confusion_matrix"]).shape == (10, 10)


def test_gbs_mnist_classifier_accepts_index_number_alias() -> None:
    dataset = load_mnist_data(train_size=50, test_size=10, source="digits", random_state=3)
    classifier = GBSMNISTClassifier(n_components=6, random_state=3)

    train = classifier.fit(dataset.train_data, dataset.train_labels, combine=False, IndexNumber=12)

    assert train["mode"] == "GBS-ELM"
    assert train["feature_count"] == 12


def test_gbs_mnist_classifier_reuses_gbs_features_across_modes() -> None:
    dataset = load_mnist_data(train_size=80, test_size=20, source="digits", random_state=5)
    classifier = GBSMNISTClassifier(n_components=8, feature_count=24, random_state=5)

    classifier.fit(dataset.train_data, dataset.train_labels, combine=True)
    rvfl_predictions = classifier.predict(dataset.test_data)
    elm_train = classifier.fit(dataset.train_data, dataset.train_labels, combine=False, reuse=True)
    elm_predictions = classifier.predict(dataset.test_data, reuse=True)

    assert elm_train["mode"] == "GBS-ELM"
    assert rvfl_predictions.shape == elm_predictions.shape


def test_run_mnist_recognition_returns_structured_result() -> None:
    result = run_mnist_recognition(
        train_size=80,
        test_size=20,
        source="digits",
        n_components=8,
        feature_count=24,
        random_state=4,
    )

    payload = result.to_dict()
    assert payload["source"] == "sklearn-digits"
    assert payload["image_shape"] == [8, 8]
    assert 0.0 <= payload["accuracy"] <= 1.0
    assert len(payload["predictions"]) == 20
    assert len(payload["confusion_matrix"]) == 10


def test_confusion_matrix_counts_labels_and_predictions() -> None:
    matrix = confusion_matrix([0, 0, 1, 2], [0, 1, 1, 2], n_classes=3)

    np.testing.assert_array_equal(
        matrix,
        np.array(
            [
                [1, 1, 0],
                [0, 1, 0],
                [0, 0, 1],
            ]
        ),
    )


def test_invalid_mnist_inputs_raise_sdk_errors() -> None:
    with pytest.raises(InvalidParameterError):
        load_mnist_data(train_size=0)
    with pytest.raises(InvalidParameterError):
        GBSMNISTClassifier(n_components=0)
    with pytest.raises(InvalidParameterError):
        confusion_matrix([0], [0, 1])
