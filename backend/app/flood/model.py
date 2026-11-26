"""Reproducible baseline logistic regression / linear classifier for flood prediction."""

import math
from typing import Any

from pydantic import BaseModel, Field


class ModelMetadata(BaseModel):
    """Reproducibility metadata and documented limitations for flood model."""

    model_name: str = "flood-baseline-logistic"
    model_version: str = "0.1.0"
    trained_at: str | None = None
    feature_names: list[str] = Field(default_factory=list)
    hyperparameters: dict[str, Any] = Field(default_factory=dict)
    limitations: list[str] = Field(
        default_factory=lambda: [
            "Baseline linear classifier; does not capture complex hydrodynamic non-linearities.",
            "Trained only on regional pilot sensors; out-of-distribution locations may degrade.",
            "Requires precipitation and river telemetry; missing inputs default to median/0.",
        ]
    )


class FloodBaselineClassifier:
    """Standardized logistic regression classifier with deterministic gradient descent."""

    def __init__(
        self,
        learning_rate: float = 0.05,
        epochs: int = 200,
        l2_reg: float = 0.01,
        decision_threshold: float = 0.5,
        version: str = "0.1.0",
    ):
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.l2_reg = l2_reg
        self.decision_threshold = decision_threshold
        self.weights: list[float] = []
        self.bias: float = 0.0
        self.feature_means: list[float] = []
        self.feature_stds: list[float] = []
        self.metadata = ModelMetadata(
            model_version=version,
            hyperparameters={
                "learning_rate": learning_rate,
                "epochs": epochs,
                "l2_reg": l2_reg,
                "decision_threshold": decision_threshold,
            },
        )

    def _sigmoid(self, z: float) -> float:
        # Prevent numerical overflow
        if z >= 30.0:
            return 1.0
        if z <= -30.0:
            return 0.0
        return 1.0 / (1.0 + math.exp(-z))

    def _standardize_fit(self, X: list[list[float]]) -> list[list[float]]:
        n_samples = len(X)
        n_features = len(X[0])
        self.feature_means = [
            sum(X[i][j] for i in range(n_samples)) / n_samples for j in range(n_features)
        ]
        self.feature_stds = []
        for j in range(n_features):
            variance = (
                sum((X[i][j] - self.feature_means[j]) ** 2 for i in range(n_samples)) / n_samples
            )
            std = math.sqrt(variance)
            self.feature_stds.append(std if std > 1e-6 else 1.0)

        return self._standardize_transform(X)

    def _standardize_transform(self, X: list[list[float]]) -> list[list[float]]:
        return [
            [(x[j] - self.feature_means[j]) / self.feature_stds[j] for j in range(len(x))]
            for x in X
        ]

    def fit(
        self,
        X: list[list[float]],
        y: list[int],
        feature_names: list[str] | None = None,
    ) -> None:
        """Fit weights using binary cross-entropy and L2 regularization."""
        if not X or not y:
            raise ValueError("Training data cannot be empty.")
        if len(X) != len(y):
            raise ValueError(f"X len ({len(X)}) does not match y len ({len(y)})")

        n_samples = len(X)
        n_features = len(X[0])

        if feature_names:
            self.metadata.feature_names = feature_names

        X_norm = self._standardize_fit(X)

        self.weights = [0.0] * n_features
        self.bias = 0.0

        for _ in range(self.epochs):
            dw = [0.0] * n_features
            db = 0.0

            for i in range(n_samples):
                z = sum(self.weights[j] * X_norm[i][j] for j in range(n_features)) + self.bias
                p = self._sigmoid(z)
                err = p - y[i]

                for j in range(n_features):
                    dw[j] += err * X_norm[i][j]
                db += err

            for j in range(n_features):
                # Gradient with L2 regularization
                grad_w = (dw[j] / n_samples) + (self.l2_reg * self.weights[j])
                self.weights[j] -= self.learning_rate * grad_w

            self.bias -= self.learning_rate * (db / n_samples)

    def predict_proba(self, X: list[list[float]]) -> list[float]:
        """Output predicted probabilities for positive class (flood)."""
        if not self.weights:
            raise RuntimeError("Model has not been fitted.")

        X_norm = self._standardize_transform(X)
        probas = []
        for x in X_norm:
            z = sum(self.weights[j] * x[j] for j in range(len(x))) + self.bias
            probas.append(self._sigmoid(z))
        return probas

    def predict(self, X: list[list[float]]) -> list[int]:
        """Output binary class predictions according to decision_threshold."""
        probas = self.predict_proba(X)
        return [1 if p >= self.decision_threshold else 0 for p in probas]
