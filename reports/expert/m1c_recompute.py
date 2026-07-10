#!/usr/bin/env python3
"""M1C measurement-correction recompute (rules and thresholds unchanged).

Purpose
-------
1) Reproduce the numbers reported by Freqtrade 2026.6 for M1C
   (base-full / x2-full / base-oos / x2-oos) directly from the report's
   complete-trade table, using the exact formulas in
   freqtrade/data/metrics.py @ tag 2026.6:
     - calculate_sharpe: mean = sum(profit_abs/starting_balance)/days_period
                         std  = np.std(per-trade returns)  (ddof=0)
                         sharpe = mean/std*sqrt(365)
     - calculate_max_drawdown: relative drawdown on the cumulative
       *realized* profit curve sampled at trade close dates only.

   Drawdown terminology — three DISTINCT quantities (only Sharpe is an
   exact reproduction of the reported field; drawdown is not):
     - freqtrade_reported_drawdown: freqtrade summary field = relative
       drawdown measured AT the point of maximum absolute (USDT) drawdown
       of the realized-profit curve (relative=False). This is what the
       M1C report prints (15.77% base-full / 16.65% x2-full).
     - realized_equity_relative_drawdown: maximum of the relative-drawdown
       series on the SAME realized-only curve (relative=True semantics).
       Printed below as `realizedRelDD` (19.21% base-full). The gap versus
       the reported field is the field-semantics issue, not a bug here.
     - daily_mtm_drawdown: maximum drawdown of the daily mark-to-market
       equity curve (the pre-registered gate metric; 23.47% base OOS).
2) Recompute the OOS run under a single pre-registered daily standard:
     - daily UTC mark-to-market account equity (flat cash days included)
     - arithmetic daily returns, rf = 0
     - Sharpe_ann = mean/std(ddof=1)*sqrt(365)
     - MaxDD on the daily equity curve
     - PSR (probabilistic Sharpe ratio) vs SR*=0
   Data: Binance daily klines fetched 2026-07-10 from
   https://data-api.binance.vision (same public source family used by the
   M1C freqtrade download). Only opens at entry/exit dates and closes
   during holding periods are used.

Conventions
-----------
- stake_i = 0.5 * equity_before_trade (tradable_balance_ratio=0.5,
  stake unlimited, max_open_trades=1, compounding).
- per-trade net profit ratios p_i for trades #18..#31 are taken verbatim
  from the M1C report table (authoritative endpoints).
- The OOS backtest (timerange 2023-11-08..2026-07-09) has its own first
  trade: BTC entered at the 2023-11-13 daily open (first Monday after the
  first in-range Sunday decision, 2023-11-12; rotation_target=BTC on that
  Sunday is proven by the full run holding BTC across it), exited
  2024-01-15 open into ETH, i.e. same exit as full-run trade #17.
  Its profit ratio is (exit_open/entry_open)*k - 1, with the fee factor k
  calibrated from the 14 fully-known OOS trades.
- Intra-trade daily marks: E_t = E_pre + S*((P_t/P_entry)*k - 1)
  (liquidation-value convention; continuous with the pinned exit value).
"""

import math
import numpy as np

START_BAL = 100_000.0

# ---------------------------------------------------------------- report data
# (pair, open_date, close_date, profit_ratio) — base cost run, report table
FULL_TRADES = [
    ("ETH", "2018-03-12", "2018-03-15", -0.202383),
    ("ETH", "2018-05-07", "2018-05-12", -0.202396),
    ("BTC", "2019-04-08", "2019-09-23",  0.933750),
    ("BTC", "2019-10-28", "2019-11-04", -0.037711),
    ("ETH", "2020-02-03", "2020-03-12", -0.202365),
    ("ETH", "2020-04-20", "2020-05-11",  0.039096),
    ("BTC", "2020-06-01", "2020-06-15", -0.014199),
    ("ETH", "2020-06-15", "2020-11-02",  0.706618),
    ("BTC", "2020-11-02", "2021-01-18",  1.595480),
    ("ETH", "2021-01-18", "2021-07-19",  0.530210),
    ("BTC", "2021-08-16", "2021-09-13", -0.023129),
    ("ETH", "2021-09-13", "2021-09-21", -0.202393),
    ("ETH", "2021-09-27", "2022-01-10",  0.027185),
    ("ETH", "2023-01-16", "2023-01-30",  0.056220),
    ("BTC", "2023-01-30", "2023-06-19",  0.106038),
    ("BTC", "2023-06-26", "2023-08-21", -0.142835),
    ("BTC", "2023-10-23", "2024-01-15",  0.387260),
    ("ETH", "2024-01-15", "2024-02-05", -0.076809),
    ("BTC", "2024-02-05", "2024-02-19",  0.220714),
    ("ETH", "2024-02-19", "2024-03-25",  0.195558),
    ("BTC", "2024-03-25", "2024-04-08",  0.028904),
    ("ETH", "2024-04-08", "2024-04-15", -0.089323),
    ("BTC", "2024-04-15", "2024-06-03",  0.028948),
    ("ETH", "2024-06-03", "2024-06-10", -0.022646),
    ("ETH", "2024-06-17", "2024-06-24", -0.058974),
    ("ETH", "2024-07-15", "2024-07-29",  0.004673),
    ("BTC", "2024-07-29", "2024-08-05", -0.150375),
    ("BTC", "2024-09-30", "2024-10-07", -0.045277),
    ("BTC", "2024-10-21", "2025-03-03",  0.361508),
    ("BTC", "2025-05-12", "2025-07-07",  0.045705),
    ("ETH", "2025-07-07", "2025-11-10",  0.389976),
]

REPORTED = {
    "base_full": dict(final=509_649.4047, sharpe=0.0750, dd=0.157711),
    "x2_full":   dict(final=486_442.6448, sharpe=0.0725, dd=0.166528),
    "base_oos":  dict(final=153_530.9308, sharpe=0.1146, dd=0.157710),
    "x2_oos":    dict(final=150_107.5001, sharpe=0.1091, dd=0.166527),
}

# ------------------------------------------------- OOS price data (fetched)
# entry_open, exit_open, closes[entry_date .. exit_date-1]
SEG = {}
SEG["T01"] = ("BTC", "2023-11-13", "2024-01-15", 37064.13, 41732.35, [
 36462.93,35551.19,37858.20,36163.51,36613.92,36568.10,37359.86,37448.78,
 35741.65,37408.34,37294.28,37713.57,37780.67,37447.43,37242.70,37818.87,
 37854.64,37723.96,38682.52,39450.35,39972.26,41991.10,44073.32,43762.69,
 43273.14,44170.99,43713.60,43789.51,41253.40,41492.39,42869.03,43022.26,
 41940.30,42278.03,41374.65,42657.80,42275.99,43668.93,43861.80,43969.04,
 43702.16,42991.50,43576.13,42508.93,43428.85,42563.76,42066.95,42140.28,
 42283.58,44179.55,44946.91,42845.23,44151.10,44145.11,43968.32,43929.02,
 46951.04,46110.00,46653.99,46339.16,42782.73,42847.99,41732.35])
SEG["T18"] = ("ETH", "2024-01-15", "2024-02-05", 2472.87, 2289.79, [
 2511.78,2587.40,2530.19,2470.81,2492.00,2472.01,2457.05,2314.20,2242.60,
 2235.02,2218.64,2267.68,2267.94,2256.90,2317.60,2343.01,2283.14,2304.28,
 2309.06,2296.49,2289.79])
SEG["T19"] = ("BTC", "2024-02-05", "2024-02-19", 42582.88, 52137.68, [
 42708.70,43098.95,44349.60,45288.65,47132.77,47751.09,48299.99,49917.27,
 49699.59,51795.17,51880.00,52124.11,51642.64,52137.67])
SEG["T20"] = ("ETH", "2024-02-19", "2024-03-25", 2881.20, 3454.99, [
 2944.80,3014.81,2967.90,2971.40,2922.24,2992.62,3112.59,3175.94,3242.36,
 3383.10,3340.09,3433.43,3421.40,3487.81,3627.76,3553.65,3818.59,3868.76,
 3883.36,3905.21,3878.47,4064.80,3979.96,4004.79,3881.70,3742.19,3523.09,
 3644.71,3520.46,3158.64,3516.53,3492.85,3336.35,3329.53,3454.98])
SEG["T21"] = ("BTC", "2024-03-25", "2024-04-08", 67210.00, 69360.38, [
 69880.01,69988.00,69469.99,70780.60,69850.54,69582.18,71280.01,69649.80,
 65463.99,65963.28,68487.79,67820.62,68896.00,69360.39])
SEG["T22"] = ("ETH", "2024-04-08", "2024-04-15", 3454.20, 3155.11, [
 3694.61,3506.39,3545.64,3502.52,3237.43,3007.01,3155.11])
SEG["T23"] = ("BTC", "2024-04-15", "2024-06-03", 65661.85, 67765.62, [
 63419.99,63793.39,61277.37,63470.08,63818.01,64940.59,64941.15,66819.32,
 66414.00,64289.59,64498.34,63770.01,63461.98,63118.62,63866.00,60672.00,
 58364.97,59060.61,62882.01,63892.04,64012.00,63165.19,62312.08,61193.03,
 63074.01,60799.99,60825.99,61483.99,62940.08,61577.49,66206.50,65235.21,
 67024.00,66915.20,66274.01,71446.62,70148.34,69166.62,67969.65,68549.99,
 69290.57,68507.67,69436.43,68398.39,67652.42,68352.17,67540.01,67766.85,
 67765.63])
SEG["T24"] = ("ETH", "2024-06-03", "2024-06-10", 3780.92, 3706.40, [
 3767.06,3810.23,3865.99,3813.46,3678.32,3681.57,3706.40])
SEG["T25"] = ("ETH", "2024-06-17", "2024-06-24", 3624.41, 3420.91, [
 3511.46,3483.42,3560.51,3513.08,3518.50,3495.75,3420.91])
SEG["T26"] = ("ETH", "2024-07-15", "2024-07-29", 3245.20, 3270.16, [
 3483.39,3444.13,3387.05,3426.50,3503.53,3517.50,3535.92,3439.60,3482.51,
 3335.81,3175.48,3274.61,3249.01,3270.16])
SEG["T27"] = ("BTC", "2024-07-29", "2024-08-05", 68249.88, 58161.00, [
 66784.69,66188.00,64628.00,65354.02,61498.33,60697.99,58161.00])
SEG["T28"] = ("BTC", "2024-09-30", "2024-10-07", 65602.01, 62819.91, [
 63327.59,60805.78,60649.28,60752.71,62086.00,62058.00,62819.91])
SEG["T29"] = ("BTC", "2024-10-21", "2025-03-03", 69032.00, 94269.99, [
 67377.50,67426.00,66668.65,68198.28,66698.33,67092.76,68021.70,69962.21,
 72736.42,72344.74,70292.01,69496.01,69374.74,68775.99,67850.01,69372.01,
 75571.99,75857.89,76509.78,76677.46,80370.01,88647.99,87952.01,90375.20,
 87325.59,91032.07,90586.92,89855.99,90464.08,92310.79,94286.56,98317.12,
 98892.00,97672.40,97900.04,93010.01,91965.16,95863.11,95643.98,97460.00,
 96407.99,97185.18,95840.62,95849.69,98587.32,96945.63,99740.84,99831.99,
 101109.59,97276.47,96593.00,101125.00,100004.29,101424.25,101420.00,
 104463.99,106058.66,106133.74,100204.01,97461.86,97805.44,97291.99,
 95186.27,94881.47,98663.58,99429.60,95791.60,94299.03,95300.00,93738.20,
 92792.05,93576.00,94591.79,96984.79,98174.18,98220.50,98363.61,102235.60,
 96954.61,95060.61,92552.49,94726.11,94599.99,94545.06,94536.10,96560.86,
 100497.35,99987.30,104077.48,104556.23,101331.57,102260.01,106143.82,
 103706.66,103910.34,104870.50,104746.85,102620.00,102082.83,101335.52,
 103733.24,104722.94,102429.56,100635.65,97700.59,101328.52,97763.13,
 96612.43,96554.35,96506.80,96444.74,96462.75,97430.82,95778.20,97869.99,
 96608.14,97500.48,97569.66,96118.12,95780.00,95671.74,96644.37,98305.00,
 96181.98,96551.01,96258.00,91552.88,88680.40,84250.09,84708.58,84349.94,
 86064.53,94270.00])
SEG["T30"] = ("BTC", "2025-05-12", "2025-07-07", 104118.00, 109203.85, [
 102791.32,104103.72,103507.82,103763.71,103463.90,103126.65,106454.26,
 105573.74,106849.99,109643.99,111696.21,107318.30,107761.91,109004.19,
 109434.79,108938.17,107781.78,105589.75,103985.48,104591.88,105642.93,
 105857.99,105376.89,104696.86,101508.68,104288.44,105552.15,105734.00,
 110263.02,110274.39,108645.12,105671.73,106066.59,105414.64,105594.01,
 106794.53,104551.17,104886.78,104658.59,103297.99,102120.01,100963.87,
 105333.93,106083.00,107340.58,106947.06,107047.59,107296.79,108356.93,
 107146.50,105681.14,108849.60,109584.78,107984.24,108198.12,109203.84])
SEG["T31"] = ("ETH", "2025-07-07", "2025-11-10", 2570.35, 3583.46, [
 2542.29,2615.25,2768.74,2951.29,2958.22,2943.28,2972.03,3013.62,3137.89,
 3371.35,3476.87,3546.92,3592.01,3756.69,3762.33,3746.21,3628.29,3706.94,
 3724.96,3741.10,3872.10,3799.00,3793.79,3810.00,3698.39,3488.20,3393.94,
 3496.74,3720.99,3612.00,3683.31,3910.31,4009.50,4260.62,4250.57,4223.22,
 4590.52,4749.30,4546.84,4439.47,4421.99,4472.33,4312.99,4075.59,4336.16,
 4225.30,4832.07,4778.40,4780.15,4376.18,4600.63,4506.71,4511.21,4360.18,
 4373.70,4391.83,4314.50,4326.50,4450.46,4297.55,4307.45,4273.14,4306.19,
 4306.37,4310.09,4349.32,4458.82,4712.16,4666.53,4604.49,4523.74,4501.29,
 4590.53,4587.66,4468.59,4480.42,4444.97,4199.08,4164.26,4152.81,3874.36,
 4032.24,4018.38,4142.16,4215.07,4145.15,4348.03,4484.35,4512.87,4487.15,
 4514.32,4684.01,4447.70,4525.72,4368.09,3829.72,3746.79,4152.29,4240.85,
 4125.02,3985.61,3894.51,3831.57,3889.21,3982.58,3979.22,3873.05,3805.53,
 3856.80,3934.88,3953.82,4158.46,4120.15,3979.20,3902.99,3805.09,3847.99,
 3873.77,3906.58,3603.83,3287.05,3424.29,3315.14,3436.05,3401.51,3583.46])

from datetime import date, timedelta

def d(s):
    y, m, dd = map(int, s.split("-"))
    return date(y, m, dd)

# ---- integrity checks on transcription
for name, (sym, d0, d1, eo, xo, closes) in SEG.items():
    n = (d(d1) - d(d0)).days
    assert len(closes) == n, f"{name}: {len(closes)} closes, expected {n}"
    if abs(closes[-1]/xo - 1) > 0.005:
        print(f"WARN {name}: last close {closes[-1]} vs exit open {xo}")
    for a, b in zip(closes, closes[1:]):
        assert abs(b/a - 1) < 0.30, f"{name}: implausible daily move {a}->{b}"

# ---- fee factor calibration from the 14 known OOS trades
ks = []
for t in FULL_TRADES[17:]:
    sym, d0, d1, p = t
    seg = next(s for s in SEG.values() if s[1] == d0 and s[0] == sym)
    R = seg[4] / seg[3]
    ks.append((1 + p) / R)
K_BASE = float(np.median(ks))
# cost x2 (0.30%/side): scale via (1-f)/(1+f) convention ratio
conv = lambda f: (1 - f) / (1 + f)
K_X2 = K_BASE * conv(0.0030) / conv(0.0015)
print(f"calibrated k(base)={K_BASE:.7f}  spread={max(ks)-min(ks):.2e}  k(x2)={K_X2:.7f}")

# OOS-run first trade profit
p_T01_base = SEG["T01"][4] / SEG["T01"][3] * K_BASE - 1
p_T01_x2   = SEG["T01"][4] / SEG["T01"][3] * K_X2 - 1
print(f"OOS first trade (BTC 2023-11-13 -> 2024-01-15): base {p_T01_base:+.4%}  x2 {p_T01_x2:+.4%}")

def to_x2(p_base):
    return (1 + p_base) * (K_X2 / K_BASE) - 1

# ------------------------------------------- freqtrade-formula reproduction
def ft_sharpe(profit_abs, days_period, starting_balance=START_BAL):
    tp = np.array(profit_abs) / starting_balance
    mean = tp.sum() / days_period
    std = np.std(tp)  # ddof=0, exactly as freqtrade
    return mean / std * math.sqrt(365)

def ft_rel_dd(profit_abs, starting_balance=START_BAL):
    cum = np.cumsum(profit_abs)
    high = np.maximum.accumulate(np.maximum(cum, 0))
    rel = ((starting_balance + high) - (starting_balance + cum)) / (starting_balance + high)
    return float(rel.max())

def run_trades(profits):
    """compound with stake = 0.5*equity; return equity path & profit_abs list"""
    eq = START_BAL
    pas = []
    for p in profits:
        pa = 0.5 * eq * p
        pas.append(pa)
        eq += pa
    return eq, pas

def report_line(tag, profits, days):
    eq, pas = run_trades(profits)
    s = ft_sharpe(pas, days)
    dd = ft_rel_dd(pas)
    r = REPORTED[tag]
    print(f"{tag:9s} final {eq:12.2f} (rep {r['final']:12.2f})  "
          f"ftSharpe {s:.4f} (rep {r['sharpe']:.4f})  "
          f"realizedRelDD {dd:.4%} vs ftReportedDD {r['dd']:.4%}")

full_base = [t[3] for t in FULL_TRADES]
full_x2 = [to_x2(p) for p in full_base]
oos_base = [p_T01_base] + full_base[17:]
oos_x2 = [p_T01_x2] + full_x2[17:]

DAYS_FULL = (d("2026-07-09") - d("2018-03-05")).days   # 3048
DAYS_OOS = (d("2026-07-09") - d("2023-11-08")).days    # 974
print(f"days_period full={DAYS_FULL} oos={DAYS_OOS}")

report_line("base_full", full_base, DAYS_FULL)
report_line("x2_full", full_x2, DAYS_FULL)
report_line("base_oos", oos_base, DAYS_OOS)
report_line("x2_oos", oos_x2, DAYS_OOS)

# --------------------------------------------- daily MTM OOS equity curve
def build_daily_equity(k):
    start, end = d("2023-11-08"), d("2026-07-09")
    idx = {}
    day, i = start, 0
    while day <= end:
        idx[day] = i
        i += 1
        day += timedelta(days=1)
    eq = np.full(len(idx), np.nan)
    eq[0] = START_BAL
    E = START_BAL
    order = sorted(SEG.items(), key=lambda kv: kv[1][1])
    pos_end_prev = start
    for name, (sym, d0s, d1s, eo, xo, closes) in order:
        d0, d1 = d(d0s), d(d1s)
        # flat days before entry
        day = pos_end_prev
        while day < d0:
            eq[idx[day]] = E
            day += timedelta(days=1)
        S = 0.5 * E
        p_exit = (xo / eo) * k - 1
        # marks on entry date .. day before exit
        for j, c in enumerate(closes):
            day = d0 + timedelta(days=j)
            eq[idx[day]] = E + S * ((c / eo) * k - 1)
        E = E + S * p_exit
        pos_end_prev = d1
    day = pos_end_prev
    while day <= end:
        eq[idx[day]] = E
        day += timedelta(days=1)
    assert not np.isnan(eq).any()
    return eq

def psr(returns, sr_star=0.0):
    r = np.asarray(returns, float)
    n = len(r)
    sr = r.mean() / r.std(ddof=1)
    g3 = float(((r - r.mean()) ** 3).mean() / r.std(ddof=0) ** 3)
    g4 = float(((r - r.mean()) ** 4).mean() / r.std(ddof=0) ** 4)
    denom = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
    z = (sr - sr_star) * math.sqrt(n - 1) / denom
    return 0.5 * (1 + math.erf(z / math.sqrt(2))), sr, g3, g4, z

def daily_stats(tag, k, rep_final):
    eq = build_daily_equity(k)
    r = np.diff(eq) / eq[:-1]
    mean, sd1 = r.mean(), r.std(ddof=1)
    sharpe = mean / sd1 * math.sqrt(365)
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq) / peak
    imax = int(dd.argmax())
    n_active = int((r != 0).sum())
    ann_ret = (eq[-1] / eq[0]) ** (365 / (len(eq) - 1)) - 1
    ann_vol = sd1 * math.sqrt(365)
    p, sr_d, g3, g4, z = psr(r)
    ra = r[r != 0]
    sharpe_active = ra.mean() / ra.std(ddof=1) * math.sqrt(365)
    print(f"\n[{tag}] daily-MTM OOS 2023-11-08..2026-07-09  ({len(eq)} pts, "
          f"{n_active} active days)")
    print(f"  final equity      {eq[-1]:12.2f}   (trade-table endpoint {rep_final:12.2f})")
    print(f"  ann return (CAGR) {ann_ret:8.4%}   ann vol {ann_vol:8.4%}")
    print(f"  Sharpe(daily,rf=0,sqrt365,ddof=1) = {sharpe:.4f}   "
          f"[active-days-only {sharpe_active:.4f}]")
    print(f"  MaxDD(daily MTM)  {dd.max():8.4%}   trough at day index {imax} "
          f"({date(2023,11,8)+timedelta(days=imax)})")
    print(f"  PSR(SR*=0) = {p:.4f}   (daily SR {sr_d:.5f}, skew {g3:.2f}, "
          f"kurt {g4:.2f}, z {z:.3f})")
    return eq

eq_base = daily_stats("base", K_BASE, REPORTED["base_oos"]["final"])
eq_x2 = daily_stats("x2", K_X2, REPORTED["x2_oos"]["final"])

# Sharpe estimation error (Lo 2002, iid approx) for the base OOS daily series
r = np.diff(eq_base) / eq_base[:-1]
sr_d = r.mean() / r.std(ddof=1)
n = len(r)
se_d = math.sqrt((1 + 0.5 * sr_d ** 2) / (n - 1))
sr_ann, se_ann = sr_d * math.sqrt(365), se_d * math.sqrt(365)
print(f"\nSharpe_ann {sr_ann:.3f}  SE {se_ann:.3f}  "
      f"95% CI [{sr_ann-1.96*se_ann:.2f}, {sr_ann+1.96*se_ann:.2f}]  (n={n} daily obs)")

# freqtrade 2026.6 calculate_p_value (t-test on per-trade returns), manual t
_, pas = run_trades(oos_base)
tr = np.array(pas) / START_BAL
t = tr.mean() / (tr.std(ddof=1) / math.sqrt(len(tr)))
print(f"per-trade t-stat (freqtrade calculate_p_value basis, OOS base): "
      f"t={t:.3f} (n=15)")

# persist daily equity for audit
import csv
with open("m1c_oos_daily_equity.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["date_utc", "equity_base", "equity_x2"])
    day = d("2023-11-08")
    for i in range(len(eq_base)):
        w.writerow([day.isoformat(), f"{eq_base[i]:.4f}", f"{eq_x2[i]:.4f}"])
        day += timedelta(days=1)
print("\nwrote m1c_oos_daily_equity.csv")
