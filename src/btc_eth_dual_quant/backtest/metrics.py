"""Performance metrics for offline M1A backtest validation."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Trade:
    symbol: str
    entry_time_ms: int
    exit_time_ms: int
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    bars_held: int


def _returns(equity_curve: list[float]) -> list[float]:
    out: list[float] = []
    for idx in range(1, len(equity_curve)):
        previous = equity_curve[idx - 1]
        out.append(0.0 if previous <= 0 else equity_curve[idx] / previous - 1.0)
    return out


def total_return(equity_curve: list[float]) -> float:
    if len(equity_curve) < 2 or equity_curve[0] == 0:
        return 0.0
    return equity_curve[-1] / equity_curve[0] - 1.0


def annualized_return(equity_curve: list[float], days: int) -> float:
    if days <= 0 or len(equity_curve) < 2 or equity_curve[0] <= 0 or equity_curve[-1] <= 0:
        return 0.0
    return (equity_curve[-1] / equity_curve[0]) ** (365.0 / days) - 1.0


def annualized_volatility(equity_curve: list[float], annualization_days: int = 365) -> float:
    returns = _returns(equity_curve)
    if len(returns) < 2:
        return 0.0
    mean = sum(returns) / len(returns)
    variance = sum((item - mean) ** 2 for item in returns) / len(returns)
    return math.sqrt(variance) * math.sqrt(annualization_days)


def sharpe(equity_curve: list[float], annualization_days: int = 365) -> float:
    vol = annualized_volatility(equity_curve, annualization_days)
    if vol == 0:
        return 0.0
    return (sum(_returns(equity_curve)) / max(len(_returns(equity_curve)), 1) * annualization_days) / vol


def max_drawdown(equity_curve: list[float]) -> float:
    peak = 0.0
    worst = 0.0
    for value in equity_curve:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def calmar(equity_curve: list[float], days: int) -> float:
    drawdown = abs(max_drawdown(equity_curve))
    if drawdown == 0:
        return 0.0
    return annualized_return(equity_curve, days) / drawdown


def win_rate(trades: list[Trade]) -> float:
    if not trades:
        return 0.0
    return sum(1 for trade in trades if trade.pnl > 0) / len(trades)


def profit_factor(trades: list[Trade]) -> float:
    wins = sum(trade.pnl for trade in trades if trade.pnl > 0)
    losses = abs(sum(trade.pnl for trade in trades if trade.pnl < 0))
    if losses == 0:
        return float("inf") if wins > 0 else 0.0
    return wins / losses


def exposure_days(positions: list[float]) -> int:
    return sum(1 for quantity in positions if quantity > 0)


def turnover(trades: list[Trade], initial_equity: float) -> float:
    if initial_equity <= 0:
        return 0.0
    traded_notional = sum((trade.entry_price + trade.exit_price) * trade.quantity for trade in trades)
    return traded_notional / initial_equity


def worst_trade(trades: list[Trade]) -> float:
    return min((trade.return_pct for trade in trades), default=0.0)


def best_trade(trades: list[Trade]) -> float:
    return max((trade.return_pct for trade in trades), default=0.0)


def consecutive_losses(trades: list[Trade]) -> int:
    current = 0
    longest = 0
    for trade in trades:
        if trade.pnl < 0:
            current += 1
            longest = max(longest, current)
        else:
            current = 0
    return longest


def trade_average_win(trades: list[Trade]) -> float:
    wins = [trade.return_pct for trade in trades if trade.pnl > 0]
    return sum(wins) / len(wins) if wins else 0.0


def trade_average_loss(trades: list[Trade]) -> float:
    losses = [trade.return_pct for trade in trades if trade.pnl < 0]
    return sum(losses) / len(losses) if losses else 0.0


def payoff_ratio(trades: list[Trade]) -> float:
    avg_loss = abs(trade_average_loss(trades))
    return trade_average_win(trades) / avg_loss if avg_loss else 0.0


def metrics_summary(equity_curve: list[float], trades: list[Trade], days: int, positions: list[float]) -> dict[str, float]:
    return {
        "total_return": total_return(equity_curve),
        "annualized_return": annualized_return(equity_curve, days),
        "annualized_volatility": annualized_volatility(equity_curve),
        "sharpe": sharpe(equity_curve),
        "max_drawdown": max_drawdown(equity_curve),
        "calmar": calmar(equity_curve, days),
        "win_rate": win_rate(trades),
        "profit_factor": profit_factor(trades),
        "exposure_days": float(exposure_days(positions)),
        "turnover": turnover(trades, equity_curve[0] if equity_curve else 0.0),
        "worst_trade": worst_trade(trades),
        "best_trade": best_trade(trades),
        "consecutive_losses": float(consecutive_losses(trades)),
    }
