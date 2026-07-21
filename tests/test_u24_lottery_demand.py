from __future__ import annotations
import unittest
from btc_eth_dual_quant.data.u24_lottery_demand import HISTORY_HOURS,LotteryDecision,evaluate_decision,evaluate_stream
def row(order=range(15)):
 symbols=tuple(f"S{i:02d}" for i in order);histories=[]
 for symbol in symbols:
  member=int(symbol[1:]);histories.append(tuple(((hour*17+member*7)%31-15)*0.0002+0.00005*member for hour in range(HISTORY_HOURS)))
 return LotteryDecision(0,symbols,tuple(histories),tuple((0,0,0,0,0,0) for _ in symbols))
class U24LotteryTests(unittest.TestCase):
 def test_deterministic_winner(self):self.assertEqual(evaluate_decision(row())["symbol"],evaluate_decision(row(reversed(range(15))))["symbol"])
 def test_bad_shape_fails(self):
  value=row();self.assertIsNone(evaluate_decision(LotteryDecision(0,value.symbols,value.completed_log_returns[:-1],value.path_displacements)))
 def test_order_guard(self):
  with self.assertRaises(ValueError):evaluate_stream([row(),row()])
if __name__=="__main__":unittest.main()
