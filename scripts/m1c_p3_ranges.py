#!/usr/bin/env python3
"""Create immutable P3 time ranges before any backtest is run."""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path


def build_ranges(start: date, end_exclusive: date) -> dict[str, str]:
    if end_exclusive <= start:
        raise ValueError("end_exclusive must be after start")
    total_days = (end_exclusive - start).days
    oos_start = start + timedelta(days=int(total_days * 0.70))
    is_days = (oos_start - start).days
    boundaries = [start + timedelta(days=int(is_days * index / 4)) for index in range(5)]

    def timerange(left: date, right: date) -> str:
        return f"{left:%Y%m%d}-{right:%Y%m%d}"

    result = {
        "M1C_START_DATE": start.isoformat(),
        "M1C_END_EXCLUSIVE": end_exclusive.isoformat(),
        "M1C_FULL_RANGE": timerange(start, end_exclusive),
        "M1C_OOS_START": oos_start.isoformat(),
        "M1C_OOS_RANGE": timerange(oos_start, end_exclusive),
    }
    for index in range(4):
        result[f"M1C_SEGMENT_{index + 1}_RANGE"] = timerange(boundaries[index], boundaries[index + 1])
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end-exclusive", type=date.fromisoformat, required=True)
    parser.add_argument("--github-env", type=Path)
    args = parser.parse_args()
    ranges = build_ranges(args.start, args.end_exclusive)
    output = "\n".join(f"{key}={value}" for key, value in ranges.items()) + "\n"
    if args.github_env:
        with args.github_env.open("a", encoding="utf-8") as handle:
            handle.write(output)
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
