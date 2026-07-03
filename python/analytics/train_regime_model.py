"""
Market-regime detection starter.

This is intentionally a placeholder for Milestone 7. The purpose of the ML
module should be risk-management context, not stock-price prediction.
"""

from __future__ import annotations

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def build_regime_features(returns: pd.DataFrame, window: int = 20) -> pd.DataFrame:
    """
    Build simple market-regime features from a return matrix.

    Features:
    - average realized volatility
    - average pairwise correlation
    - equal-weight drawdown proxy
    """
    equal_weight_returns = returns.mean(axis=1)
    cumulative = (1.0 + equal_weight_returns).cumprod()
    drawdown = cumulative / cumulative.cummax() - 1.0

    features = pd.DataFrame(index=returns.index)
    features["realized_volatility"] = returns.rolling(window).std().mean(axis=1)
    features["average_correlation"] = returns.rolling(window).corr().groupby(level=0).mean().mean(axis=1)
    features["drawdown"] = drawdown

    return features.dropna()


def fit_regime_classifier(features: pd.DataFrame, n_clusters: int = 3) -> pd.Series:
    """
    Fit an unsupervised regime classifier.

    The cluster labels are numeric. In the dashboard, you can map them to
    calm/normal/stressed by ranking clusters on realized volatility.
    """
    scaler = StandardScaler()
    matrix = scaler.fit_transform(features)

    model = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = model.fit_predict(matrix)

    return pd.Series(labels, index=features.index, name="regime")
