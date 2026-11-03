#!/usr/bin/env python3
"""Evaluate a leakage-resistant persistence baseline on chronological AQI holdout data.

The ID_Date field is expected to contain a stable series identifier followed by
an ISO date, e.g. AS_4_2022-12-04. Each series is evaluated independently.
Only prior observed AQI values are used as predictions.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import sys
from datetime import date
from pathlib import Path

ID_DATE_PATTERN = re.compile(r"^(?P<series>.+)_(?P<date>\d{4}-\d{2}-\d{2})$")


def load_series(path: Path) -> dict[str, list[tuple[date, float]]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, strict=True)
        fieldnames = reader.fieldnames or []
        if len(fieldnames) != len(set(fieldnames)):
            raise ValueError("train CSV contains duplicate column names")
        fields = set(fieldnames)
        if not {"ID_Date", "AQI"}.issubset(fields):
            raise ValueError("train CSV must contain ID_Date and AQI columns")
        series: dict[str, list[tuple[date, float]]] = {}
        for line, row in enumerate(reader, start=2):
            if None in row:
                raise ValueError(f"line {line}: row contains more fields than the header")
            key = (row.get("ID_Date") or "").strip()
            match = ID_DATE_PATTERN.fullmatch(key)
            if not match:
                raise ValueError(f"line {line}: ID_Date must end with YYYY-MM-DD: {key!r}")
            raw = (row.get("AQI") or "").strip()
            try:
                value = float(raw)
            except ValueError as exc:
                raise ValueError(f"line {line}: AQI must be numeric, got {raw!r}") from exc
            if not math.isfinite(value):
                raise ValueError(f"line {line}: AQI must be finite")
            try:
                parsed_date = date.fromisoformat(match.group("date"))
            except ValueError as exc:
                raise ValueError(f"line {line}: ID_Date contains an invalid calendar date: {key!r}") from exc
            series.setdefault(match.group("series"), []).append((parsed_date, value))
    if not series:
        raise ValueError("train CSV contains no records")
    for key, rows in series.items():
        rows.sort(key=lambda item: item[0])
        dates = [item[0] for item in rows]
        if len(dates) != len(set(dates)):
            raise ValueError(f"duplicate date in series {key!r}")
        if len(rows) < 3:
            raise ValueError(f"series {key!r} needs at least 3 rows for chronological evaluation")
    return series


def _metrics(errors: list[float]) -> dict[str, float | int]:
    if not errors:
        raise ValueError("no held-out rows available")
    return {
        "test_rows": len(errors),
        "mae": sum(abs(error) for error in errors) / len(errors),
        "rmse": math.sqrt(sum(error * error for error in errors) / len(errors)),
    }


def evaluate(
    series: dict[str, list[tuple[date, float]]], test_fraction: float = 0.2
) -> dict[str, object]:
    if not 0.05 <= test_fraction <= 0.5:
        raise ValueError("test fraction must be between 0.05 and 0.5")
    all_errors: list[float] = []
    first_test_date: date | None = None
    last_test_date: date | None = None
    per_series: dict[str, dict[str, object]] = {}
    for key, rows in sorted(series.items()):
        split = max(2, math.floor(len(rows) * (1.0 - test_fraction)))
        split = min(split, len(rows) - 1)
        # One-step-ahead persistence uses the previous observed value in this series.
        errors = [rows[index][1] - rows[index - 1][1] for index in range(split, len(rows))]
        test_dates = [rows[index][0] for index in range(split, len(rows))]
        all_errors.extend(errors)
        series_start, series_end = min(test_dates), max(test_dates)
        first_test_date = min(first_test_date, series_start) if first_test_date else series_start
        last_test_date = max(last_test_date, series_end) if last_test_date else series_end
        per_series[key] = {
            **_metrics(errors),
            "test_start": series_start.isoformat(),
            "test_end": series_end.isoformat(),
        }
    aggregate = _metrics(all_errors)
    return {
        "baseline": "previous_observation",
        "series": len(per_series),
        **aggregate,
        "test_start": first_test_date.isoformat() if first_test_date else "",
        "test_end": last_test_date.isoformat() if last_test_date else "",
        "per_series": per_series,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=Path("dataset/train.csv"))
    parser.add_argument("--test-fraction", type=float, default=0.2)
    parser.add_argument("--output", type=Path, help="Optional JSON output path")
    args = parser.parse_args()
    try:
        metrics = evaluate(load_series(args.data), args.test_fraction)
    except (OSError, ValueError) as exc:
        print(f"Evaluation failed: {exc}", file=sys.stderr)
        return 2
    import json
    rendered = json.dumps(metrics, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
