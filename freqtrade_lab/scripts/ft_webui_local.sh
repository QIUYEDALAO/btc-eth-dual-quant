#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

bash scripts/ft_no_live_guard.sh

CONFIG="user_data/configs/config.dryrun.example.json"

if grep -n -E '"dry_run"[[:space:]]*:[[:space:]]*false' "$CONFIG"; then
  echo "安全检查失败：dry_run 不是 true。"
  exit 1
fi

if grep -n -E '"(key|token|password)"[[:space:]]*:[[:space:]]*"[^"<][^"]{3,}"' "$CONFIG"; then
  echo "安全检查失败：配置中疑似存在真实凭据。"
  exit 1
fi

if grep -n -E '"(trading_mode|runmode)"[[:space:]]*:[[:space:]]*"live"' "$CONFIG"; then
  echo "安全检查失败：配置中疑似存在 live 模式。"
  exit 1
fi

echo "WebUI 将只绑定服务器本地端口 127.0.0.1:8080。"
echo "请用 SSH tunnel 访问：ssh -L 8080:127.0.0.1:8080 \$VPS_HOST"
echo "然后浏览器打开：http://127.0.0.1:8080"
echo "不要开放公网端口，不要配置 API key，不要用于实盘。"

exec bash scripts/ft_research.sh webserver --config "$CONFIG"
