# Cookie Cats: where should the first gate go?

A/B test analysis of a real mobile puzzle game. In Cookie Cats, players hit "gates" that force them to wait or pay
before continuing. The team tested moving the first gate from **level 30** to **level 40** and randomly assigned
players to each version.

**Data:** public Cookie Cats dataset, `data/cookie_cats.csv`. It has 90,189 players, one row each:
`version` (gate_30 or gate_40), `sum_gamerounds` (rounds played in the first 14 days), and `retention_1` and
`retention_7` (whether the player came back 1 and 7 days after installing).
**Run:** `python analysis/ab_test.py` (needs pandas, numpy, scipy, matplotlib). Results go to `outputs/results.json`,
and the chart goes to `outputs/d7_bootstrap.png`.

## Results

| Metric | gate_30 | gate_40 | Difference | Significance |
|---|---|---|---|---|
| Players | 44,699 | 45,489 | | |
| Day-1 retention | 44.82% | 44.23% | +0.59 pts | p = 0.074 (not significant); 95% CI −0.07 to +1.24 |
| **Day-7 retention** | **19.02%** | **18.20%** | **+0.82 pts** | **p = 0.0016; 95% CI +0.31 to +1.33; P(gate_30 better) = 99.9%** |
| Median rounds played | 17 | 16 | | Mann-Whitney p = 0.051 |

**Recommendation: keep the gate at level 30.** Moving it to 40 doesn't help day-1 retention and lowers day-7 retention
by 0.82 points. That's about 4.5% fewer players returning in week 1, or roughly 820 fewer day-7 players per
100K installs.

**Why might an earlier gate retain better?** Players get a forced break sooner, which may stop them burning out on
the game in their first days. That's a hypothesis to test, not something this data proves.

## Checks and caveats

- **Sample ratio mismatch.** The split should be 50/50, but the groups are 45,489 vs 44,700 (chi-square p = 0.009).
  Before trusting the result in production, I'd check how players were assigned (for example, whether one version
  dropped some installs or logging). The retention gap is large relative to its noise, so it's unlikely to be
  explained by this alone, but it has to be checked.
- **One outlier removed.** One player logged 49,854 rounds in 14 days, almost certainly a logging or bot issue.
- **Rounds are not levels.** `sum_gamerounds` counts rounds played, not the level reached, so I can't say exactly
  how many players actually reached the gate. 36.9% played at least 30 rounds, and 30.4% played at least 40.
- **Retention only.** There's no revenue or purchase data, so this can't say whether the later gate made more money
  from players paying to skip it.
- **Statistics used:** two-proportion z-test for retention, a bootstrap with 10,000 resamples for confidence
  intervals, and Mann-Whitney U for rounds played, because that data is heavily skewed. 4.4% of players never
  played a single round.

## What I'd do next in a LiveOps team

1. Fix or explain the sample ratio mismatch, then re-run the test.
2. Add guardrail metrics: revenue per user, and the share of players who pay to skip the gate.
3. Track day-14 and day-30 retention to see whether the gap holds or closes.
