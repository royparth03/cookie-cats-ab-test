"""Cookie Cats gate experiment: should the first gate sit at level 30 or level 40?

Data: data/cookie_cats.csv (public Cookie Cats dataset, 90,189 players randomly assigned).
Columns: userid, version (gate_30 / gate_40), sum_gamerounds (rounds played in first 14 days),
retention_1 / retention_7 (came back 1 / 7 days after install).

Run:  python analysis/ab_test.py      ->  prints results, writes outputs/
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "outputs")
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(42)
B = 10_000  # bootstrap resamples


def two_prop_ztest(x1, n1, x2, n2):
    p = (x1 + x2) / (n1 + n2)
    se = np.sqrt(p * (1 - p) * (1 / n1 + 1 / n2))
    z = (x1 / n1 - x2 / n2) / se
    return z, 2 * (1 - stats.norm.cdf(abs(z)))


def main():
    df = pd.read_csv(os.path.join(ROOT, "data", "cookie_cats.csv"))
    res = {"players": int(len(df))}

    # 1. Sample ratio check: was the 50/50 split respected?
    counts = df["version"].value_counts()
    chi2, p_srm = stats.chisquare(counts.values)
    res["group_sizes"] = counts.to_dict()
    res["srm_p_value"] = float(p_srm)

    # 2. Data quality: one player logged ~50K rounds in 14 days; drop as a logging outlier.
    top = int(df["sum_gamerounds"].max())
    df = df[df["sum_gamerounds"] < top].copy()
    res["dropped_outlier_rounds"] = top
    res["players_after_cleaning"] = int(len(df))
    res["never_played_pct"] = round(100 * (df["sum_gamerounds"] == 0).mean(), 1)

    # 3. Retention by group + significance
    g = df.groupby("version")
    summary = g.agg(players=("userid", "size"), d1=("retention_1", "mean"),
                    d7=("retention_7", "mean"), median_rounds=("sum_gamerounds", "median"))
    res["by_group"] = summary.round(4).to_dict(orient="index")

    a, b = df[df.version == "gate_30"], df[df.version == "gate_40"]
    for k in ("retention_1", "retention_7"):
        z, p = two_prop_ztest(a[k].sum(), len(a), b[k].sum(), len(b))
        # bootstrap the difference in retention (gate_30 minus gate_40), in percentage points
        diffs = np.empty(B)
        av, bv = a[k].to_numpy(), b[k].to_numpy()
        for i in range(B):
            diffs[i] = rng.choice(av, len(av)).mean() - rng.choice(bv, len(bv)).mean()
        lo, hi = np.percentile(diffs, [2.5, 97.5]) * 100
        res[k] = {"gate_30_pct": round(100 * av.mean(), 2), "gate_40_pct": round(100 * bv.mean(), 2),
                  "diff_pp": round(100 * (av.mean() - bv.mean()), 2),
                  "ci95_pp": [round(lo, 2), round(hi, 2)],
                  "p_value": round(float(p), 4),
                  "prob_gate30_better": round(float((diffs > 0).mean()), 3)}
        if k == "retention_7":
            d7_diffs = diffs

    # 4. Engagement: rounds played (heavily skewed, so Mann-Whitney rather than t-test)
    u, p_mw = stats.mannwhitneyu(a["sum_gamerounds"], b["sum_gamerounds"])
    res["rounds_mannwhitney_p"] = round(float(p_mw), 4)

    # 5. Where players drop off: share still playing after N rounds
    res["share_reaching_rounds"] = {
        str(n): round(100 * (df["sum_gamerounds"] >= n).mean(), 1) for n in (1, 10, 30, 40, 100)}

    # 6. What the 7-day gap means at scale
    res["d7_players_lost_per_100k_installs"] = round(1000 * res["retention_7"]["diff_pp"])

    with open(os.path.join(OUT, "results.json"), "w") as f:
        json.dump(res, f, indent=2, default=str)

    # Chart: bootstrap distribution of the 7-day retention gap
    plt.figure(figsize=(6, 3.2))
    plt.hist(d7_diffs * 100, bins=60, color="#4c72b0")
    plt.axvline(0, color="black", lw=1)
    plt.xlabel("7-day retention: gate_30 minus gate_40 (percentage points)")
    plt.ylabel("bootstrap samples")
    plt.title("Gate at level 30 keeps more players at day 7")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT, "d7_bootstrap.png"), dpi=150)

    print(json.dumps(res, indent=2, default=str))


if __name__ == "__main__":
    main()
