import json, unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from btc_eth_dual_quant.data.liquid_universe import *
from scripts.liquid_universe_public_run import archive_timestamp

ROOT=Path(__file__).resolve().parents[1]; CONTRACT=json.loads((ROOT/'config/liquid_spot_universe_contract.json').read_text())
def evidence(symbol, start, count, volume=100):
    return [DailyEvidence(symbol,start+timedelta(days=i),Decimal(volume),"monthly",f"{symbol}-{i}") for i in range(count)]

class QualificationTests(unittest.TestCase):
    def test_archive_millisecond_and_microsecond_timestamps_match(self):
        self.assertEqual(archive_timestamp('1704067200000'),archive_timestamp('1704067200000000'))
    def test_daily_only_fills_and_never_overwrites(self):
        d=date(2020,1,1); m=DailyEvidence('BTCUSDT',d,Decimal(1),'monthly','m'); x=DailyEvidence('BTCUSDT',d,Decimal(9),'daily','d')
        self.assertEqual(merge_daily([m],[x])[0],m)
    def test_prior_window_history_and_tie_break(self):
        effective=date(2021,1,1); start=effective-timedelta(days=365)
        rows=evidence('ETHUSDT',start,365)+evidence('BTCUSDT',start,365)
        result=build_month(effective,rows,CONTRACT)
        self.assertEqual([x.symbol for x in result],['BTCUSDT','ETHUSDT'])
        future=DailyEvidence('ZZZUSDT',effective,Decimal(999999),'monthly','future')
        self.assertEqual(build_month(effective,rows,CONTRACT),build_month(effective,rows+[future],CONTRACT))
    def test_spike_does_not_dominate_median_and_short_history_rejected(self):
        e=date(2021,1,1); s=e-timedelta(days=365); a=evidence('AAAUSDT',s,365,100); a[-1]=DailyEvidence('AAAUSDT',a[-1].day,Decimal(999999),'monthly','spike')
        rows=a+evidence('BBBUSDT',s,365,101)+evidence('CCCUSDT',e-timedelta(days=364),364,1000)
        self.assertEqual([x.symbol for x in build_month(e,rows,CONTRACT)],['BBBUSDT','AAAUSDT'])
    def test_exclusions_and_delisted_history(self):
        e=date(2021,1,1); s=e-timedelta(days=365); rows=evidence('USDCUSDT',s,365,1000)+evidence('OLDUSDT',s,365,10)
        self.assertEqual([x.symbol for x in build_month(e,rows,CONTRACT)],['OLDUSDT'])
    def test_exact_twelve_bar_aggregation_and_hash(self):
        t=datetime(2024,1,1,tzinfo=timezone.utc); bars=[MinuteBar('BTCUSDT',t+timedelta(minutes=5*i),Decimal(1),Decimal(3),Decimal(0),Decimal(2),Decimal('0.1')) for i in range(12)]
        self.assertEqual(aggregate_one_hour(bars).volume,Decimal('1.2'))
        with self.assertRaises(ValueError): aggregate_one_hour(bars[:-1])
        rows=build_month(date(2021,1,1),evidence('BTCUSDT',date(2020,1,2),365),CONTRACT)
        self.assertEqual(membership_hash(rows),membership_hash(rows))
if __name__=='__main__': unittest.main()
