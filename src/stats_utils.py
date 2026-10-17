"""Phase 6: bootstrap and hypothesis-testing helpers."""
import numpy as np
from sklearn.metrics import roc_auc_score, average_precision_score

RNG_SEED = 42


def boot_idx(n, n_boot, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    return rng.integers(0, n, size=(n_boot, n))


def percentile_ci(x, level=0.95):
    a = (1 - level) / 2
    return float(np.quantile(x, a)), float(np.quantile(x, 1 - a))


def bootstrap_metric(y, scores, fn, n_boot=2000, seed=RNG_SEED):
    """Percentile bootstrap of fn(y, scores) over test rows. Skips degenerate resamples."""
    idx = boot_idx(len(y), n_boot, seed)
    out = []
    for i in idx:
        if y[i].min() == y[i].max():
            continue
        out.append(fn(y[i], scores[i]))
    return np.array(out)


def top_frac_stats(y, p, frac=0.2):
    k = int(frac * len(y))
    top = np.argsort(-p)[:k]
    caught = y[top].sum()
    return caught / k, caught / y.sum(), (caught / k) / y.mean()   # precision, recall, lift


def bootstrap_paired_diff(y, p1, p2, fn, n_boot=2000, seed=RNG_SEED):
    idx = boot_idx(len(y), n_boot, seed)
    d = []
    for i in idx:
        if y[i].min() == y[i].max():
            continue
        d.append(fn(y[i], p1[i]) - fn(y[i], p2[i]))
    return np.array(d)


def cohens_h(p1, p2):
    return 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))
