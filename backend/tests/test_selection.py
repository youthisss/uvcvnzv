from datetime import time

import pandas as pd

from app.selection import select_day_ahead, select_horizon


def fc(rows):
    df = pd.DataFrame(rows, columns=["startTime", "publishTime", "generation"])
    for c in ("startTime", "publishTime"):
        df[c] = pd.to_datetime(df[c], utc=True)
    return df


def test_day_ahead_picks_latest_before_gate_not_globally_latest():
    f = fc([
        ("2026-01-15T12:00Z", "2026-01-14T02:30Z", 100),
        ("2026-01-15T12:00Z", "2026-01-14T07:30Z", 110),
        ("2026-01-15T12:00Z", "2026-01-14T09:30Z", 120),  # after the 09:00 gate
        ("2026-01-15T12:00Z", "2026-01-15T02:30Z", 999),  # same day: pure look-ahead
    ])
    out = select_day_ahead(f, time(9, 0))
    assert len(out) == 1
    assert out.generation.iloc[0] == 110
    assert out.publishTime.iloc[0] == pd.Timestamp("2026-01-14T07:30Z")


def test_publish_exactly_at_gate_is_included():
    f = fc([("2026-01-15T00:00Z", "2026-01-14T09:00Z", 5)])
    assert len(select_day_ahead(f, time(9, 0))) == 1


def test_target_without_pre_gate_forecast_is_missing():
    f = fc([("2026-01-15T00:00Z", "2026-01-14T09:30Z", 5)])
    assert select_day_ahead(f, time(9, 0)).empty


def test_gate_is_configurable():
    f = fc([
        ("2026-01-15T12:00Z", "2026-01-14T07:30Z", 110),
        ("2026-01-15T12:00Z", "2026-01-14T09:30Z", 120),
    ])
    assert select_day_ahead(f, time(10, 0)).generation.iloc[0] == 120


def test_early_january_target_uses_late_december_publish():
    f = fc([
        ("2026-01-01T03:00Z", "2025-12-31T07:30Z", 7),
        ("2026-01-01T03:00Z", "2026-01-01T02:30Z", 8),
    ])
    out = select_day_ahead(f, time(9, 0))
    assert out.generation.iloc[0] == 7


def test_duplicate_start_publish_pairs_keep_last():
    f = fc([
        ("2026-01-15T12:00Z", "2026-01-14T07:30Z", 1),
        ("2026-01-15T12:00Z", "2026-01-14T07:30Z", 2),
    ])
    out = select_day_ahead(f, time(9, 0))
    assert len(out) == 1 and out.generation.iloc[0] == 2


def test_each_target_selected_independently():
    f = fc([
        ("2026-01-15T00:00Z", "2026-01-14T07:30Z", 1),
        ("2026-01-16T00:00Z", "2026-01-14T07:30Z", 2),  # D-1 for the 16th is the 15th: still valid
        ("2026-01-16T00:00Z", "2026-01-15T07:30Z", 3),
    ])
    out = select_day_ahead(f, time(9, 0)).set_index("startTime").generation
    assert out[pd.Timestamp("2026-01-15T00:00Z")] == 1
    assert out[pd.Timestamp("2026-01-16T00:00Z")] == 3


def test_gate_follows_uk_wall_clock_in_summer():
    # BST: 09:00 local == 08:00 UTC, so an 08:30 UTC publish is after the gate.
    f = fc([
        ("2026-07-15T12:00Z", "2026-07-14T07:30Z", 1),
        ("2026-07-15T12:00Z", "2026-07-14T08:30Z", 2),
    ])
    assert select_day_ahead(f, time(9, 0)).generation.iloc[0] == 1


def test_horizon_mode_latest_publish_at_least_h_before_target():
    f = fc([
        ("2026-01-15T12:00Z", "2026-01-15T02:30Z", 1),  # 9.5h before
        ("2026-01-15T12:00Z", "2026-01-15T07:30Z", 2),  # 4.5h before
        ("2026-01-15T12:00Z", "2026-01-15T09:30Z", 3),  # 2.5h before
    ])
    assert select_horizon(f, 4).generation.iloc[0] == 2
    assert select_horizon(f, 2).generation.iloc[0] == 3
    assert select_horizon(f, 12).empty


def test_empty_input():
    f = fc([])
    assert select_day_ahead(f, time(9, 0)).empty
    assert select_horizon(f, 6).empty
