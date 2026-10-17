"""Phase 4: customer segmentation (K-Means on scaled + one-hot features, Ward as a sanity check).

The churn label is NOT used to build clusters. It is only used afterwards to profile them.
"""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score, davies_bouldin_score, adjusted_rand_score
from sklearn.pipeline import Pipeline

NUM = ["tenure", "MonthlyCharges", "n_protective"]
CAT = ["Contract", "InternetService", "PaymentMethod", "PaperlessBilling", "SeniorCitizen",
       "Partner", "Dependents", "PhoneService", "MultipleLines", "StreamingTV", "StreamingMovies"]
SEED = 42


def make_preprocessor() -> ColumnTransformer:
    return ColumnTransformer([
        ("num", StandardScaler(), NUM),
        ("cat", OneHotEncoder(drop="if_binary", sparse_output=False), CAT),
    ])


def make_features(df: pd.DataFrame, n_components=0.90):
    """Scale numerics, one-hot categoricals, then PCA keeping `n_components` of the variance."""
    pipe = Pipeline([("prep", make_preprocessor()), ("pca", PCA(n_components=n_components, random_state=SEED))])
    return pipe, pipe.fit_transform(df)


def scan_k(X, ks=range(2, 11)):
    rows = []
    for k in ks:
        km = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(X)
        rows.append({"k": k, "inertia": km.inertia_,
                     "silhouette": silhouette_score(X, km.labels_),
                     "davies_bouldin": davies_bouldin_score(X, km.labels_)})
    return pd.DataFrame(rows)


def stability(X, k, n_boot=30, frac=0.8):
    """Mean Adjusted Rand Index between full-data labels and labels from 80% subsamples."""
    rng = np.random.default_rng(SEED)
    full = KMeans(n_clusters=k, n_init=20, random_state=SEED).fit(X)
    aris = []
    for b in range(n_boot):
        idx = rng.choice(len(X), int(frac * len(X)), replace=False)
        sub = KMeans(n_clusters=k, n_init=10, random_state=b).fit(X[idx])
        aris.append(adjusted_rand_score(full.labels_[idx], sub.labels_))
    return float(np.mean(aris)), float(np.std(aris))


def fit_kmeans(X, k):
    return KMeans(n_clusters=k, n_init=50, random_state=SEED).fit(X)


def ward_agreement(X, k, km_labels):
    w = AgglomerativeClustering(n_clusters=k, linkage="ward").fit_predict(X)
    return w, adjusted_rand_score(km_labels, w)


def profile(df, labels):
    d = df.assign(cluster=labels)
    g = d.groupby("cluster")
    out = pd.DataFrame({
        "customers": g.size(),
        "pct_base": (g.size() / len(d) * 100).round(1),
        "churn_rate_pct": (g.Churn.mean() * 100).round(1),
        "share_of_churners_pct": (g.Churn.sum() / d.Churn.sum() * 100).round(1),
        "avg_tenure": g.tenure.mean().round(1),
        "avg_monthly": g.MonthlyCharges.mean().round(1),
        "avg_protective": g.n_protective.mean().round(2),
        "top_contract": g.Contract.agg(lambda s: s.value_counts().index[0]),
        "pct_top_contract": g.Contract.agg(lambda s: round(100 * s.value_counts(normalize=True).iloc[0])),
        "top_internet": g.InternetService.agg(lambda s: s.value_counts().index[0]),
        "pct_echeck": g.PaymentMethod.agg(lambda s: round(100 * (s == "Electronic check").mean())),
    })
    out["monthly_revenue"] = g.MonthlyCharges.sum().round(0)
    return out


def name_segments(prof: pd.DataFrame) -> dict:
    """Map cluster ids to business names using their profile (robust to label permutation, k=4)."""
    names = {}
    names[prof.avg_monthly.idxmin()] = "Budget phone-only"
    rest = prof.drop(index=list(names))
    names[rest.churn_rate_pct.idxmax()] = "At-risk fiber, month-to-month"
    rest = prof.drop(index=list(names))
    names[rest.avg_tenure.idxmax()] = "Loyal premium"
    names[prof.drop(index=list(names)).index[0]] = "Mid-tier DSL, month-to-month"
    return names
