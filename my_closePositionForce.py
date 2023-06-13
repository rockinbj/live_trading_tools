import sys

from my_functions import *

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option("display.unicode.ambiguous_as_wide", True)
pd.set_option("display.unicode.east_asian_width", True)


print("如果需要清仓, 请加入'--close'参数")
print("如果需要平仓指定币种, 请加入'--close=symbol'参数, 例如--close=ETH/USDT，仓位全平")
print("如果需要平仓指定比例, 请加入 比例 参数, 例如--close=ETH/USDT 0.5 即平ETH的 50% 仓位")
print("\n")

ex = getattr(ccxt, EXCHANGE_ID)(EXCHANGE_CONFIG)
mkts = ex.loadMarkets()

pos = getOpenPosition(ex)
pos = pos[["side", "contracts", "notional", "unrealizedPnl", "percentage", "leverage", "entryPrice", "markPrice",
           "liquidationPrice", "marginType", "datetime"]]
pos.sort_values("percentage", ascending=False, inplace=True)
print(f"当前持仓情况:\n{pos}\n")
bal = getBalance(ex, asset="USDT")
print(f"当前余额:\n{bal}\n")

close_pct = 1.0

if len(sys.argv) == 3 and is_float(sys.argv[2]):
    close_pct = float(sys.argv[2])
    del sys.argv[2]

if len(sys.argv) == 2:
    if "--close" == sys.argv[1]:
        print(f"\n\n\n正在执行清仓操作......\n")
        closePositionForce(exchange=ex, markets=mkts, openPositions=pos, close_pct=close_pct)

        pos = getOpenPosition(ex)
        pos = pos[
            ["side", "contracts", "notional", "unrealizedPnl", "percentage", "leverage", "entryPrice", "markPrice",
             "liquidationPrice", "marginType", "datetime"]]
        pos.sort_values("percentage", ascending=False, inplace=True)
        print(f"清仓之后的持仓情况:\n{pos}")
        bal = getBalance(ex)
        print(f"清仓之后的余额:\n{bal}")

    elif "--close=" in sys.argv[1]:
        symbol = sys.argv[1].replace("--close=", "")
        print(f"\n\n\n正在执行{symbol}的平仓操作.....\n")
        closePositionForce(exchange=ex, markets=mkts, openPositions=pos, symbol=symbol, close_pct=close_pct)

        pos = getOpenPosition(ex)
        pos = pos[
            ["side", "contracts", "notional", "unrealizedPnl", "percentage", "leverage", "entryPrice", "markPrice",
             "liquidationPrice", "marginType", "datetime"]]
        pos.sort_values("percentage", ascending=False, inplace=True)
        print(f"清仓之后的持仓情况:\n{pos}")
        bal = getBalance(ex)
        print(f"清仓之后的余额:\n{bal}")
