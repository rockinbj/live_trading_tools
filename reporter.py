from my_functions import *

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 100)
pd.set_option('display.max_columns', 100)
pd.set_option("display.unicode.ambiguous_as_wide", True)
pd.set_option("display.unicode.east_asian_width", True)
logger = logging.getLogger("app.reptr")


DATA_PATH = DB_PATH
os.makedirs(DATA_PATH, exist_ok=True)


def runReporter(exchange):
    unPnl, equity, accountPositions = loadDataFromExchange(exchange)
    equityFile, positionFile = saveDataToFile(unPnl, equity, accountPositions)

    # equityFile, positionFile = r"data/dbFiles/equityFile.pkl", r"data/dbFiles/positionFile.pkl"
    picFile = drawPic(equityFile, positionFile)
    picUrl = uploadPic(picFile)
    sendReport(unPnl, equity, accountPositions, picUrl)


def main():
    ex = getattr(ccxt, EXCHANGE_ID)(EXCHANGE_CONFIG)

    while True:
        sleepToClose(REPORT_INTERVAL, aheadSeconds=0, isTest=TEST_REPORT, offsetSec=-59)

        runReporter(ex)

        time.sleep(0.1)
        if TEST_REPORT: exit()


if __name__ == '__main__':
    main()
