#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FAIL=0

flag() {
  printf 'M1F guard finding: %s\n' "$1"
  FAIL=1
}

if grep -R -n -E '"dry_run"[[:space:]]*:[[:space:]]*false' "$ROOT/user_data/configs" 2>/dev/null; then
  flag "dry_run disabled in a config"
fi

if grep -R -n -E '"(key|token|password)"[[:space:]]*:[[:space:]]*"[^"<][^"]{3,}"' "$ROOT/user_data/configs" 2>/dev/null; then
  flag "credential-like value in a config"
fi

if grep -R -n -E '"(trading_mode|runmode)"[[:space:]]*:[[:space:]]*"live"' "$ROOT/user_data/configs" 2>/dev/null; then
  flag "live run mode in a config"
fi

trade_word="tr""ade"
if grep -R --exclude='ft_no_live_guard.sh' -n -E "freqtrade[[:space:]]+${trade_word}|command:[[:space:]]*.*${trade_word}" "$ROOT" 2>/dev/null; then
  flag "unsafe trade command in freqtrade_lab"
fi

order_word="order"
if grep -R --exclude='ft_no_live_guard.sh' -n -E "/api/v3/${order_word}|/fapi/v1/${order_word}|create_${order_word}|cancel_${order_word}|place_${order_word}" "$ROOT" 2>/dev/null; then
  flag "direct trading endpoint or SDK method reference in freqtrade_lab"
fi

if [[ "$FAIL" -ne 0 ]]; then
  echo "M1F no-live guard FAIL"
  exit 1
fi

echo "M1F no-live guard PASS"
