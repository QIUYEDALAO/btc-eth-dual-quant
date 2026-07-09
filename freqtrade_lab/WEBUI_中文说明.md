# Freqtrade WebUI 中文说明

## 当前 WebUI 的定位

当前 WebUI 只是 M1F Freqtrade feasibility 研究环境，用来确认 Freqtrade 作为研究、回测、数据下载、日志查看和 WebUI 候选框架是否可用。

它不是实盘交易系统，不代表策略已经通过验证，也不允许连接真实交易 API。

## 如何通过 SSH tunnel 打开

在你的本机终端执行：

```bash
ssh -L 8080:127.0.0.1:8080 $VPS_HOST
```

保持这个 SSH 窗口不要关闭，然后在本机浏览器访问：

```text
http://127.0.0.1:8080
```

推荐使用 SSH tunnel，而不是把 WebUI 暴露到公网。

## 英文菜单中文对照表

| English | 中文 |
| --- | --- |
| Dashboard | 总览 |
| Trades | 交易记录 |
| Open Trades | 当前持仓 |
| Backtesting | 回测 |
| Strategies | 策略 |
| Config | 配置 |
| Logs | 日志 |
| Profit | 盈亏统计 |
| Pairlist | 交易对列表 |
| Settings | 设置 |
| Start | 启动 |
| Stop | 停止 |
| Force exit | 强制退出/强制平仓 |
| Reload config | 重载配置 |
| Dry-run | 虚拟运行 |
| Live | 实盘 |

## 哪些页面可以看

- Dashboard: 看 WebUI 是否在线、当前状态是什么。
- Strategies: 看当前策略文件是否能被 Freqtrade 识别。
- Backtesting: 做离线回测相关操作。
- Logs: 看启动、配置校验、数据下载、回测是否报错。
- Config: 确认配置仍然是研究模式，没有真实交易凭据。

## 哪些按钮暂时不要点

- Start bot
- Force exit
- 任何 live 相关按钮
- 任何 API key 配置
- 任何真实交易配置

当前阶段只允许研究和回测。即使页面上有控制按钮，也不代表本项目允许使用它们。

## 如何确认当前不是实盘

检查配置时必须同时满足：

- `dry_run` 必须为 `true`。
- config 里不能有 API key。
- `trading_mode` 当前必须是 `spot`。
- 没有真实 exchange credentials。
- 没有账户余额、真实持仓、真实资金流水。

如果任何一项不满足，立即停止 WebUI，并回到安全检查清单排查。

## 如何确认只在做研究

当前只允许运行这些命令类型：

- `backtesting`
- `download-data`
- `show-config`
- `version`

这些操作只用于研究、配置检查、公开数据下载和离线回测。

## 常见错误解释

### Docker 没启动

现象：命令提示无法连接 Docker daemon。

处理：确认 VPS 已安装 Docker，并且 Docker 服务正在运行。

### 端口访问不了

现象：浏览器打不开 `http://127.0.0.1:8080`。

处理：确认 SSH tunnel 窗口仍然开着，确认 WebUI 脚本正在运行，确认端口是 `8080`。

### strategy 找不到

现象：页面或日志提示找不到 `M1ATrendValidationStrategy`。

处理：确认 `freqtrade_lab/user_data/strategies/M1ATrendValidationStrategy.py` 存在。

### pair 数据没下载

现象：回测提示 BTC/USDT 或 ETH/USDT 没有数据。

处理：先运行公开数据下载脚本，再运行回测脚本。

### config 校验失败

现象：日志出现 configuration validation 错误。

处理：查看 Config 和 Logs，确认仍然使用 `config.dryrun.example.json`，并确认没有填入真实凭据。

### WebUI 空白

现象：浏览器页面空白或加载不出来。

处理：刷新页面，检查容器日志，确认 WebUI 容器仍在运行，确认 SSH tunnel 没断。

## 当前阶段结论

当前 M1A 趋势策略已经 `failed_validation`，不得用于实盘。

M1F 只是 Freqtrade 框架可行性验证。它只能证明 Freqtrade Lab 能部署、能打开 WebUI、能下载公开数据、能运行回测 smoke，不能证明策略盈利。

资金费套利仍需要外部协调器，不得直接用 WebUI 交易。
