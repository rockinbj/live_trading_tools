import sys
import time

from my_functions import *
from my_settings import _config

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option("display.unicode.ambiguous_as_wide", True)
pd.set_option("display.unicode.east_asian_width", True)
logger = logging.getLogger("app.reptr")


def runReporter(exchange):
    unPnl, equity, accountPositions = loadDataFromExchange(exchange)
    equityFile, positionFile = saveDataToFile(unPnl, equity, accountPositions)

    equityPicFile = drawPic(equityFile, positionFile)
    equityPicUrl = uploadPic(equityPicFile)

    if name_of_index:
        index_pic_file = draw_indexcta_pic(file_of_index_cta_csv,
                                           len_short=_config.account_config[name_of_index]["strategy"]["para"][0],
                                           len_long=_config.account_config[name_of_index]["strategy"]["para"][1],
                                           )
        index_pic_url = uploadPic(index_pic_file)
        sendReport(unPnl, equity, accountPositions, equityPicUrl, index_pic_url)
    else:
        sendReport(unPnl, equity, accountPositions, equityPicUrl)


def main():
    ex = getattr(ccxt, EXCHANGE_ID)(EXCHANGE_CONFIG)

    while True:
        sleepToClose(REPORT_INTERVAL, aheadSeconds=0, isTest=TEST_REPORT, offsetSec=-59)

        retryy(runReporter, "runReporter() in main()", exchange=ex)

        time.sleep(0.1)
        if TEST_REPORT: exit()


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "--test":
        TEST_REPORT = True

    while True:
        try:
            main()
        except Exception as e:
            sendAndPrintError(f"日志模块主程序接到异常, 重新启动, 请尽快检查日志: {e}")
            logger.exception(e)
            time.sleep(10)
            continue
