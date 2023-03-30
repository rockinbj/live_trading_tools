import time
import datetime as dt
from pathlib import Path
import base64

import ccxt
import pandas as pd
import requests
import matplotlib.pyplot as plt
import matplotlib.dates as mpl_dates

from my_settings import *
from my_logger import *
logger = logging.getLogger("app.func")
DATA_PATH = Path(DB_PATH)


def sendMixin(msg, _type="PLAIN_TEXT"):
    token = MIXIN_TOKEN
    url = f"https://webhook.exinwork.com/api/send?access_token={token}"

    value = {
        'category': _type,
        'data': msg,
    }

    msg = f"来自 {RUN_NAME}:\n" + msg

    try:
        r = requests.post(url, data=value, timeout=2).json()
    except Exception as err:
        logger.exception(err)


def sendAndPrintError(msg):
    logger.error(msg)
    sendMixin(msg)


def callAlarm(strategyName=RUN_NAME, content="存在严重风险项, 请立即检查"):
    url = "http://api.aiops.com/alert/api/event"
    apiKey = CALLKEY
    eventId = str(int(time.time()))
    stragetyName = strategyName
    content = content
    para = f"?app={apiKey}&eventType=trigger&eventId={eventId}&priority=3&host={stragetyName}&alarmContent={content}"

    try:
        r = requests.post(url + para)
        if r.json()["result"] != "success":
            sendAndPrintError(f"电话告警触发失败, 可能有严重风险, 请立即检查！{r.text}")
    except Exception as e:
        logger.error(f"电话告警触发失败, 可能有严重风险, 请立即检查！{e}")
        logger.exception(e)


def sendAndCritical(msg):
    logger.critical(msg)
    if CALL_ALARM:
        callAlarm(strategyName=RUN_NAME, content=msg)
    sendMixin(msg)


def sendAndRaise(msg):
    logger.error(msg)
    sendMixin(msg)
    raise RuntimeError(msg)


def retryy(func, _name="retryy", _wait=1, _times=3, critical=False, **kwargs):
    error = ""
    for i in range(_times):
        try:
            return func(**kwargs)
        except ccxt.MarginModeAlreadySet:
            pass
        except Exception as e:
            error = str(e)
            logger.error(f"{_name} raised a error: {e}")
            logger.exception(e)
            time.sleep(_wait)
    else:
        f = f"{RUN_NAME} {_name} 重试{_times}次无效, 程序退出: {error}"
        if critical:
            sendAndCritical("！严重级别告警！" + f)
        else:
            sendAndPrintError(f)
        raise RuntimeError(f)


def getPositions(exchange):
    # positions:
    # info    id  contracts  contractSize  unrealizedPnl  leverage liquidationPrice  collateral  notional markPrice  entryPrice timestamp  initialMargin  initialMarginPercentage  maintenanceMargin  maintenanceMarginPercentage marginRatio datetime marginMode marginType  side  hedged percentage
    try:
        p = exchange.fetchPositions()
        p = pd.DataFrame(p)
        p.set_index("symbol", inplace=True)
        p.index.name = None
        return p
    except Exception as e:
        logger.exception(e)
        sendAndRaise(f"{RUN_NAME}: getPositions()错误, 程序退出。{e}")


def getOpenPosition(exchange):
    pos = getPositions(exchange)
    op = pd.DataFrame()
    op = pos.loc[pos["contracts"] != 0]
    op = op.astype(
        {
            "contracts": float,
            "unrealizedPnl": float,
            "leverage": float,
            "liquidationPrice": float,
            "collateral": float,
            "notional": float,
            "markPrice": float,
            "entryPrice": float,
            "marginType": str,
            "side": str,
            "percentage": float,
            "timestamp": "datetime64[ms]",
        }
    )
    op = op[["side", "contracts", "notional", "percentage", "unrealizedPnl", "leverage", "entryPrice", "markPrice",
             "liquidationPrice", "marginType", "datetime", "timestamp"]]
    return op


def getBalance(exchange, asset="usdt"):
    # 返回不包含uPNL的账户权益，即 已开仓占用的保证金 和 可用余额 的总和
    asset = asset.upper()
    r = exchange.fapiPrivateGetAccount()["assets"]
    r = pd.DataFrame(r)
    bal = float(r.loc[r["asset"] == asset, "walletBalance"])
    return bal


def closePositionForce(exchange, markets, openPositions, symbol=None):
    # 如果没有symbol参数, 清空所有持仓, 如果有symbol只平仓指定币种
    for s, pos in openPositions.iterrows():
        if symbol is not None and s != symbol: continue
        symbolId = markets[s]["id"]
        para = {
            "symbol": symbolId,
            "side": "SELL" if pos["side"]=="long" else "BUY",
            "type": "MARKET",
            "quantity": pos["contracts"],
            "reduceOnly": True,
        }

        retryy(exchange.fapiPrivatePostOrder, critical=True, params=para)


def loadDataFromExchange(exchange):
    # return unPnl, equity, positions
    total, balances, accountPositions = getAccountBalance(exchange)
    positions = getOpenPosition(exchange)

    # 获取余额
    total["totalMarginBalance"] = total["totalMarginBalance"].astype(float).round(2)
    total["totalCrossUnPnl"] = total["totalCrossUnPnl"].astype(float).round(2)
    equity = total.iloc[0]["totalMarginBalance"]
    unPnl = total.iloc[0]["totalCrossUnPnl"]

    # 获取持仓
    positions[[
        "notional", "percentage",
        "unrealizedPnl", "entryPrice",
        "markPrice", "liquidationPrice"]] = \
        positions[[
            "notional", "percentage",
            "unrealizedPnl", "entryPrice",
            "markPrice", "liquidationPrice"]]\
            .astype(float).round(2)
    positions["datetime"] = pd.to_datetime(positions["datetime"])
    positions["datetime"] = positions["datetime"].dt.strftime('%Y-%m-%d %H:%M:%S')
    positions['timestamp'] = positions['timestamp'].values.astype('int64') // 10 ** 6
    positions.reset_index(inplace=True)
    positions.rename(columns={"index": "symbol"}, inplace=True)

    logger.debug(f"loadData: unPnl={unPnl} equity={equity} positions=\n{positions}")
    return unPnl, equity, positions


def saveDataToFile(unPnl, equity, positions):
    # return equityFile, positionFile

    os.makedirs(str(DATA_PATH), exist_ok=True)
    equityFile = DATA_PATH / "equityFile.pkl"
    positionFile = DATA_PATH / "positionFile.pkl"

    # 保存equity文件
    if os.path.isfile(equityFile):
        equityDf = pd.read_pickle(equityFile)
    else:
        equityDf = pd.DataFrame(columns=["equity", "unPnl", "saveTime"])

    newEquityRow = pd.DataFrame(
        {"equity": equity, "unPnl": unPnl, "saveTime": time.time()},
        index=[0]
    )
    equityDf = pd.concat([equityDf, newEquityRow], ignore_index=True)
    equityDf.to_pickle(equityFile)

    # 保存position文件
    if os.path.isfile(positionFile):
        positionDf = pd.read_pickle(positionFile)
    else:
        positionDf = pd.DataFrame(columns=[
            "symbol",
            "side",
            "contracts",
            "notional",
            "percentage",
            "unrealizedPnl",
            "leverage",
            "entryPrice",
            "markPrice",
            "liquidationPrice",
            "marginType",
            "datetime",
            "timestamp",
            "saveTime",
        ])

    positions["saveTime"] = time.time()
    positionDf = pd.concat([positionDf, positions], ignore_index=True)
    positionDf.to_pickle(positionFile)

    return equityFile, positionFile


def sendReport(*args):
    [unPnl, equity, posOri, picUrl] = args
    pos = posOri.copy()

    logger.debug("开始发送报告")
    msg = f"### {RUN_NAME} - 策略报告\n\n"
    msg += f"#### 账户权益 : {equity}U\n"
    msg += f"资金曲线 :\n![equityPic.png]({picUrl})\n"

    if pos.shape[0] > 0:
        pos.set_index("symbol", inplace=True)
        pos = pos[
            [
                "side",
                "notional",
                "percentage",
                "unrealizedPnl",
                "entryPrice",
                "markPrice",
                "liquidationPrice",
                "datetime",
                "leverage",
            ]
        ]
        pos["datetime"] = pd.to_datetime(pos["datetime"]) + dt.timedelta(hours=8)
        pos["datetime"] = pos["datetime"].dt.floor("s")

        pos.rename(
            columns={
                "side": "持仓方向",
                "notional": "持仓价值(U)",
                "percentage": "盈亏比例(%)",
                "unrealizedPnl": "未实现盈亏(U)",
                "entryPrice": "开仓价格(U)",
                "markPrice": "当前价格(U)",
                "liquidationPrice": "爆仓价格(U)",
                "datetime": "开仓时间",
                "leverage": "页面杠杆",
            },
            inplace=True,
        )

        pos.sort_values(by="盈亏比例(%)", ascending=False, inplace=True)
        d = pos.to_dict(orient="index")

        msg += f"#### 账户盈亏 : {unPnl}U\n"
        msg += f'#### 当前持币 : {", ".join([i.split("/")[0] for i in list(d.keys())])}'

        for k, v in d.items():
            msg += f"""
##### {k.split("/")[0]}
- 持仓方向    : {v["持仓方向"]}
- 持仓价值(U) : {v["持仓价值(U)"]}
- 盈亏比例(%) : {v["盈亏比例(%)"]}
- 未实现盈亏(U) : {v["未实现盈亏(U)"]}
- 开仓价格(U) : {v["开仓价格(U)"]}
- 当前价格(U) : {v["当前价格(U)"]}
- 爆仓价格(U) : {v["爆仓价格(U)"]}
- 开仓时间 : {v["开仓时间"]}
- 页面杠杆 : {v["页面杠杆"]}
"""
    else:
        msg += "#### 当前空仓\n"

    msg += f"#### 页面杠杆 : {PAGE_LEVERAGE}\n"
    msg += f"#### 资金上限 : {MAX_BALANCE * 100}%\n"
    msg += f"#### 实际杠杆 : {round(PAGE_LEVERAGE * MAX_BALANCE, 2)}\n"
    msg += f"#### 因子名称 : {FACTOR_NAME}\n"
    msg += f"#### 因子参数 : {FACTOR_PARAMS}\n"

    sendMixin(msg, _type="PLAIN_POST")


def drawPic(equityFile, posFile):
    eqDf = pd.read_pickle(equityFile)
    eqDf["saveTime"] = pd.to_datetime(eqDf["saveTime"], unit="s").dt.floor("s") + dt.timedelta(hours=8)
    eqDf.sort_values("saveTime", inplace=True)
    unPnl = eqDf.loc[eqDf["saveTime"] == eqDf["saveTime"].max(), "unPnl"].squeeze()

    # 找出最近持仓情况
    posDf = pd.read_pickle(posFile)
    posNow = posDf.loc[posDf["saveTime"] == posDf["saveTime"].max()]
    posNow["datetime"] = pd.to_datetime(posNow["datetime"]) + dt.timedelta(hours=8)
    posNow = posNow.sort_values("percentage", ascending=False)
    posNow = posNow[[
        "symbol",
        "side",
        "notional",
        "percentage",
        "unrealizedPnl",
        "datetime",
    ]]
    posNow.rename(columns={
        "side": "方向",
        "notional": "持仓价值",
        "percentage": "盈亏比",
        "unrealizedPnl": "未实现盈亏",
        "datetime": "开仓时间",
    }, inplace=True)
    posNow.set_index("symbol", drop=True, inplace=True)
    posNow.index.name = None

    # 计算最高点与现在的回撤
    eq_now = eqDf.iloc[-1]["equity"]
    eq_max = eqDf["equity"].max()
    drawdown = eq_now / eq_max - 1
    drawdown = f"{round(drawdown*100,1)}%"

    # 计算今日收益率
    eqDf_1d = eqDf.set_index("saveTime").resample("1D").last()
    day_pct = eqDf_1d["equity"].pct_change().iloc[-1]
    day_pct = f"{round(day_pct*100,1)}%"

    # 计算年化收益率
    eq1d_first = eqDf_1d.iloc[0]["equity"]
    eq1d_now = eqDf_1d.iloc[-1]["equity"]
    annual_return = pow(eq1d_now/eq1d_first, 365/len(eqDf_1d)) - 1
    annual_return = f"{round(annual_return,1)}倍"

    # 画资金曲线
    fig, ax = plt.subplots(figsize=(15, 10), facecolor='black')
    ax.plot(eqDf["saveTime"], eqDf["equity"], color="tab:green")
    ax.xaxis.set_major_formatter(mpl_dates.DateFormatter('%Y-%m-%d %H:%M:%S'))  # 调整时间轴格式
    ax.xaxis.set_major_locator(mpl_dates.AutoDateLocator())
    plt.ylabel("USDT 余额 (包含未实现盈亏)")
    plt.title(f"{RUN_NAME} 策略 资金曲线")
    fig.autofmt_xdate()

    # 图上标注文字
    comment = f"总未实现盈亏: {unPnl}U, 今日盈亏: {day_pct}, 预期年化: {annual_return}, 回撤: {drawdown}\n\n" \
              f"持仓情况:\n" \
              f"{posNow}"
    ax.annotate(
        comment,
        xy=(0.05, 0.01),
        xycoords="axes fraction",
        textcoords="offset pixels",
        xytext=(-100, 30),
        bbox=dict(boxstyle="square,pad=0.3", fc="black", ec="tab:green", lw=1),
        color="white",
    )

    # 优化一些图片显示
    # 显示中文
    plt.rcParams['font.sans-serif'] = ["SimHei"]  # 中文San-serif字体
    plt.rcParams['axes.unicode_minus'] = False  # 解决负号'-'显示为方块的问题

    # 去掉上边框和右边框
    ax.spines['top'].set_color('none')
    ax.spines['right'].set_color('none')
    # 调整plot.show()的空白边框
    plt.subplots_adjust(left=0.1, top=0.9, right=0.95, bottom=0.15)

    # 设置黑色背景
    ax.set_facecolor('black')  # 设置坐标轴背景色为黑色
    # 调整坐标轴的颜色和标签颜色
    ax.tick_params(axis='x', colors='white')
    ax.tick_params(axis='y', colors='white')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    # 设置 x 轴横线颜色和 y 轴竖线颜色
    ax.spines['bottom'].set_color('white')
    ax.spines['left'].set_color('white')

    fileName = DATA_PATH / "equityPic.jpg"
    logger.debug(f"保存资金曲线图片 {fileName}")
    plt.savefig(fileName, bbox_inches='tight', dpi=200)
    # plt.show()
    plt.close()

    return fileName


def uploadPic(fileName):
    return upload_pic_imgbb(fileName)


def upload_pic_smms(file):
    headers = {"Authorization": IMG_TOKEN}
    files = {"smfile": open(file, "rb")}
    url = "https://smms.app/api/v2/upload"
    r = requests.post(url, files=files, headers=headers).json()
    if r["success"]:
        logger.debug(f"上传图片成功")
        picUrl = r["data"]["url"]
        return picUrl
    else:
        logger.warning(f"图片上传失败")
        logger.warning(r)
        return None


def upload_pic_imgbb(file):
    url = "https://api.imgbb.com/1/upload"
    params = {
        "expiration": (3600 * 24) * 15,
        "key": IMG_TOKEN,
    }

    image_path = file
    with open(image_path, "rb") as image_file:
        b64 = base64.b64encode(image_file.read()).decode('utf-8')
        data = {"image": b64}

    try:
        response = requests.post(url, params=params, data=data).json()
        if response["success"]:
            img_link = response["data"]["display_url"]
            logger.debug(f"上传图片成功: {img_link}")
        else:
            img_link = "https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png"
            logger.warning(f"图片上传失败: {response}")
    except Exception as e:
        img_link = "https://user-images.githubusercontent.com/24848110/33519396-7e56363c-d79d-11e7-969b-09782f5ccbab.png"
        logger.warning(f"图片上传失败")
        logger.exception(e)

    return img_link


def nextStartTime(level, ahead_seconds=3, offsetSec=0):
    # ahead_seconds为预留秒数,
    # 当离开始时间太近, 本轮可能来不及下单, 因此当离开始时间的秒数小于预留秒数时,
    # 就直接顺延至下一轮开始
    if level.endswith('m') or level.endswith('h'):
        pass
    elif level.endswith('T'):
        level = level.replace('T', 'm')
    elif level.endswith('H'):
        level = level.replace('H', 'h')
    else:
        sendAndRaise(f"{RUN_NAME}: level格式错误。程序退出。")

    ti = pd.to_timedelta(level)
    now_time = dt.datetime.now()
    # now_time = dt.datetime(2019, 5, 9, 23, 50, 30)  # 修改now_time, 可用于测试
    this_midnight = now_time.replace(hour=0, minute=0, second=0, microsecond=0)
    min_step = dt.timedelta(minutes=1)

    target_time = now_time.replace(second=0, microsecond=0)

    while True:
        target_time = target_time + min_step
        delta = target_time - this_midnight
        if (
                delta.seconds % ti.seconds == 0
                and (target_time - now_time).seconds >= ahead_seconds
        ):
            # 当符合运行周期, 并且目标时间有足够大的余地, 默认为60s
            break

    target_time -= dt.timedelta(seconds=offsetSec)
    return target_time


def sleepToClose(level, aheadSeconds, isTest=False, offsetSec=0):
    nextTime = nextStartTime(level, ahead_seconds=aheadSeconds, offsetSec=offsetSec)
    testStr = f"(测试轮, 跳过等待时间)" if isTest else ""
    logger.info(f"等待开始时间: {nextTime} {testStr}")
    if isTest is False:
        time.sleep(max(0, (nextTime - dt.datetime.now()).seconds))
        while True:  # 在靠近目标时间时
            if dt.datetime.now() > nextTime:
                break
    logger.info(f"吉时已到, 开炮!")
    return nextTime


def getAccountBalance(exchange):
    # positions:
    # initialMargin maintMargin unrealizedProfit positionInitialMargin openOrderInitialMargin leverage  isolated entryPrice maxNotional positionSide positionAmt notional isolatedWallet updateTime bidNotional askNotional
    try:
        b = retryy(exchange.fetchBalance, _name=f"获取账户资金信息getBalances()")["info"]
        balances = pd.DataFrame(b["assets"])
        balances.set_index("asset", inplace=True)
        balances.index.name = None
        positions = pd.DataFrame(b["positions"])
        positions.set_index("symbol", inplace=True)
        positions.index.name = None
        b.pop("assets")
        b.pop("positions")
        total = pd.DataFrame(b, index=[0])
        return total, balances, positions
    except Exception as e:
        logger.exception(e)
        sendAndPrintError(f"{RUN_NAME}: getAccountBalance()错误: {e}")
