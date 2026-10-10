# Controlled synthetic-pattern evaluation

Run `.\.venv\Scripts\python.exe -m scripts.evaluate` after retrieving the pinned official CSV. `results.json` records the configuration, source hash, exclusions, every source-row reference and synthetic modification. The October 10 rerun reproduced all cases and metrics; only generation time changes.

Q1 2024 was development data. Q2 2024 supplies 25 non-overlapping windows and 150 paired controlled cases, using the same stations (not spatial generalization). Configuration was saved before Q2 evaluation; no subsequent tuning is claimed. Source values remain unchanged on disk.

Resolution and publication/operating assumptions are synthetic benchmark metadata, not verified CGWB metadata. Unmodified controls are not independently certified fault-free. Abstained positive cases count as false negatives; abstained controls are excluded from the executed-control false-positive denominator and separately counted. Detection latency is conditional source-clock latency, not measured live service latency.

This evaluates detection of controlled synthetic anomaly patterns. It does not establish accuracy for diagnosing real physical sensor failures.
