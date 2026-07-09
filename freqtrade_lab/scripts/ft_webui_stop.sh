#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

echo "正在停止 Freqtrade Lab 相关容器。"
docker compose stop freqtrade >/dev/null 2>&1 || true
docker compose rm -f -s freqtrade >/dev/null 2>&1 || true
docker rm -f btc_eth_dual_quant_freqtrade_lab >/dev/null 2>&1 || true
docker rm -f btc_eth_dual_quant_freqtrade_webui >/dev/null 2>&1 || true
echo "已停止 WebUI/实验容器。没有删除数据、配置或报告。"
