"""Phase 5: churn modelling pipelines, evaluation helpers and a leakage-safe segment feature."""
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_validate
from sklearn.metrics import (roc_auc_score, average_precision_score, precision_recall_fscore_support,
                             confusion_matrix)
from imblearn.pipeline import Pipeline as ImbPipeline
from imblearn.over_sampling import SMOTE

from src import segment as S

SEED = 42
TARGET = "Churn"
# TotalCharges ~ tenure x MonthlyCharges (redundant, and hurts coefficient interpretability).
DROP = ["customerID", "TotalCharges", "tenure_bucket", "n_protective", TARGET]


def split_xy(df):
    X = df.drop(columns=[c for c in DROP if c in df.columns])
    return X, df[TARGET].values


def preprocessor(X: pd.DataFrame, scale=True) -> ColumnTransformer:
    num = [c for c in X.columns if X[c].dtype != object and X[c].nunique() > 2]
    cat = [c for c in X.columns if c not in num]
    return ColumnTransformer([
        ("num", StandardScaler() if scale else "passthrough", num),
        ("cat", OneHotEncoder(drop="if_binary", sparse_output=False, handle_unknown="ignore"), cat),
    ])


class SegmentFeature(BaseEstimator, TransformerMixin):
    """Adds a K-Means segment id (one-hot). Clustering is fit ONLY on the data passed to fit(),
    i.e. the training fold, so no information from validation/test rows leaks into the feature."""
    def __init__(self, k=4):
        self.k = k

    def fit(self, X, y=None):
        X = X.copy()
        X["n_protective"] = sum((X[c] == "Yes").astype(int) for c in
                                ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"])
        self.pipe_, Z = S.make_features(X)
        self.km_ = S.fit_kmeans(Z, self.k)
        return self

    def transform(self, X):
        X = X.copy()
        X["n_protective"] = sum((X[c] == "Yes").astype(int) for c in
                                ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport"])
        lab = self.km_.predict(self.pipe_.transform(X))
        out = X.drop(columns="n_protective")
        out["segment_id"] = lab.astype(str)
        return out


def make_model(name, X, imbalance="none", with_segment=False):
    clf = {
        "logreg": LogisticRegression(max_iter=2000, C=1.0, random_state=SEED,
                                     class_weight="balanced" if imbalance == "class_weight" else None),
        "rf": RandomForestClassifier(n_estimators=400, min_samples_leaf=5, n_jobs=-1, random_state=SEED,
                                     class_weight="balanced_subsample" if imbalance == "class_weight" else None),
        "hgb": HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, random_state=SEED,
                                              class_weight="balanced" if imbalance == "class_weight" else None),
    }[name]
    Xe = X.assign(segment_id="0") if with_segment else X
    steps = []
    if with_segment:
        steps.append(("segment", SegmentFeature()))
    steps.append(("prep", preprocessor(Xe, scale=(name == "logreg"))))
    if imbalance == "smote":
        steps.append(("smote", SMOTE(random_state=SEED)))
        steps.append(("clf", clf))
        return ImbPipeline(steps)
    steps.append(("clf", clf))
    return Pipeline(steps)


def cv_scores(model, X, y, n_splits=5):
    cv = StratifiedKFold(n_splits, shuffle=True, random_state=SEED)
    r = cross_validate(model, X, y, cv=cv, scoring={"roc_auc": "roc_auc", "pr_auc": "average_precision"}, n_jobs=1)
    return {k: (r[f"test_{k}"].mean(), r[f"test_{k}"].std()) for k in ["roc_auc", "pr_auc"]}


def oof_proba(model, X, y, n_splits=5):
    cv = StratifiedKFold(n_splits, shuffle=True, random_state=SEED)
    return cross_val_predict(model, X, y, cv=cv, method="predict_proba")[:, 1]


def best_f1_threshold(y, p):
    ts = np.linspace(0.05, 0.95, 91)
    f = [precision_recall_fscore_support(y, p >= t, average="binary", zero_division=0)[2] for t in ts]
    return float(ts[int(np.argmax(f))])


def lift_table(y, p, revenue=None, bins=10):
    d = pd.DataFrame({"y": y, "p": p})
    if revenue is not None:
        d["rev"] = revenue
        d["lost_rev"] = d.rev * d.y
    d = d.sort_values("p", ascending=False).reset_index(drop=True)
    d["decile"] = (np.arange(len(d)) * bins // len(d)) + 1
    g = d.groupby("decile")
    t = pd.DataFrame({"customers": g.size(), "churners": g.y.sum(), "churn_rate": g.y.mean()})
    t["lift"] = t.churn_rate / d.y.mean()
    t["cum_churners_captured"] = t.churners.cumsum() / d.y.sum()
    if revenue is not None:
        t["cum_lost_mrr_captured"] = g.lost_rev.sum().cumsum() / d.lost_rev.sum()
    return t


def threshold_metrics(y, p, t):
    pr, rc, f1, _ = precision_recall_fscore_support(y, p >= t, average="binary", zero_division=0)
    tn, fp, fn, tp = confusion_matrix(y, p >= t).ravel()
    return {"threshold": round(t, 2), "precision": pr, "recall": rc, "f1": f1, "tp": tp, "fp": fp, "fn": fn, "tn": tn}
