#!/usr/bin/env python3
"""Emit deterministic, result-free Freqtrade strategy runtime identities."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from freqtrade.resolvers import StrategyResolver


def canonical_hash(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_value(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        return {str(key): json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_value(item) for item in value]
    return str(value)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--strategy-path", type=Path, default=Path("/strategy"))
    parser.add_argument("--original-path", type=Path, default=Path("/original/original_source.py"))
    parser.add_argument("--user-data-dir", type=Path, default=Path("/freqtrade/user_data"))
    args = parser.parse_args()

    config = {
        "strategy": args.candidate,
        "strategy_path": str(args.strategy_path),
        "user_data_dir": args.user_data_dir,
    }
    strategy = StrategyResolver.load_strategy(config)
    strategy.ft_load_hyper_params(False)

    setting_names = [
        "timeframe", "minimal_roi", "stoploss", "trailing_stop",
        "trailing_stop_positive", "trailing_stop_positive_offset",
        "trailing_only_offset_is_reached", "use_exit_signal",
        "exit_profit_only", "ignore_roi_if_entry_signal", "order_types",
        "order_time_in_force", "position_adjustment_enable",
        "max_entry_position_adjustment", "can_short", "startup_candle_count",
        "process_only_new_candles",
    ]
    settings = {name: json_value(getattr(strategy, name, None)) for name in setting_names}
    parameters = {
        name: {
            "value": json_value(parameter.value),
            "range": json_value(list(parameter.range)),
            "load": bool(parameter.load),
            "optimize": bool(parameter.optimize),
        }
        for name, parameter in sorted(strategy.enumerate_parameters(), key=lambda item: item[0])
    }
    adapter = args.strategy_path / "adapter.py"
    dependency_files = sorted(
        path for path in args.strategy_path.rglob("*.py") if path != adapter
    )
    executable = {
        "adapter_sha256": file_hash(adapter),
        "original_sha256": file_hash(args.original_path),
        "dependencies": {
            str(path.relative_to(args.strategy_path)): file_hash(path)
            for path in dependency_files
        },
    }
    parameter_files = sorted(args.user_data_dir.rglob(f"{args.candidate}.json"))
    result = {
        "schema_version": "external-strategy-runtime-probe-v1",
        "candidate_id": args.candidate,
        "base_adapter_hash": executable["adapter_sha256"],
        "variant_executable_hash": canonical_hash(executable),
        "runtime_effective_settings": settings,
        "runtime_effective_settings_hash": canonical_hash(settings),
        "runtime_resolved_parameters": parameters,
        "runtime_resolved_parameters_hash": canonical_hash(parameters),
        "observed_external_parameter_file_count": len(parameter_files),
        "observed_config_override_count": 0,
        "position_increase_capability": bool(settings["position_adjustment_enable"]),
        "can_short": bool(settings["can_short"]),
        "executable_components": executable,
    }
    print(json.dumps(result, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
