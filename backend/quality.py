"""Quality is scoped to the pilot window and use, never physical water safety."""
from collections import Counter, defaultdict
from datetime import timedelta

from .models import Observation, Quality
from .provider import START, END

CADENCE = 21600


def assess(records: list[Observation], window_start=START, window_end=END):
    by_time = defaultdict(list)
    times = [row.source_time for row in records if row.source_time is not None]
    for row in records:
        if row.source_time is not None:
            by_time[row.source_time].append(row)
    duplicate_count = sum(len(group) - 1 for group in by_time.values())
    conflicts = sum(len({row.raw_numeric_value for row in group}) > 1 for group in by_time.values())
    clean = []
    for stamp, group in sorted(by_time.items()):
        if len({row.raw_numeric_value for row in group}) == 1 and group[0].raw_numeric_value is not None:
            clean.append(group[0])
    # Expected grid phase comes from modal observed source-clock remainder,
    # not an assumed UTC/IST offset. Off-grid records remain visible.
    remainders = Counter(int((stamp - window_start).total_seconds()) % CADENCE for stamp in times)
    phase = remainders.most_common(1)[0][0] if remainders else 0
    grid = set()
    slot = window_start + timedelta(seconds=phase)
    while slot < window_end:
        grid.add(slot)
        slot += timedelta(seconds=CADENCE)
    occupied = {row.source_time for row in clean} & grid
    off_grid = sum(stamp not in grid for stamp in times)
    intervals = [(b.source_time - a.source_time).total_seconds() for a, b in zip(clean, clean[1:])]
    missing_run = longest_run = 0
    for slot in sorted(grid):
        missing_run = 0 if slot in occupied else missing_run + 1
        longest_run = max(longest_run, missing_run)
    reasons = ["Physical meaning, sign, datum and timezone unverified; original values preserved.", "Station grouping is provisional; no verified official station identifier.", "Provider sentinel dictionary and device diagnostics unavailable.", "Completeness uses nominal six-hour cadence and observed modal grid phase; it is not publication uptime."]
    if duplicate_count:
        reasons.append("Duplicate timestamps retained in audit; conflicting slots excluded from analysis.")
    if off_grid:
        reasons.append("Off-grid acquisitions are counted separately from expected slots.")
    state = "INSUFFICIENT" if len(clean) < 21 else "POOR" if conflicts else "LIMITED"
    return Quality(window_start=window_start, window_end_exclusive=window_end, state=state, raw_rows=len(records), valid_unique_observations=len(clean), numeric_invalid=sum(row.raw_numeric_value is None for row in records), timestamp_invalid=sum(row.source_time is None for row in records), duplicate_timestamps=duplicate_count, conflicting_timestamps=conflicts, out_of_order=sum(b < a for a, b in zip(times, times[1:])), expected_slots=len(grid), occupied_slots=len(occupied), completeness=len(occupied) / len(grid), off_grid_count=off_grid, longest_gap_seconds=longest_run * CADENCE, available_history_seconds=sum(intervals), reasons=reasons), clean
