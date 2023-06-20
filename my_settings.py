import sys
import os
import importlib
from pathlib import Path


# ↓↓↓以下需配置↓↓↓
# 实盘config文件的绝对路径
file_of_live_config = r"xxx/config.py"
# 实盘交易所文件的绝对路径
file_of_exchange_config = r"xxx/exchangeConfig.py"

# 指数择时专用：指数名称，指数实盘框架中，config.py中account_config里配置的名称，如：TrashBox01
# 指数名称 留空 则不画图：
name_of_index = ""
# 如果需要画指数择时的信号图，需要指明 指数文件路径
file_of_index_cta_csv = r"xxx/GameFi.csv"
# ↑↑↑以上需配置↑↑↑

path_of_live_config, filename_of_live_config = os.path.split(file_of_live_config)
path_of_exchange_config, filename_of_exchange_config = os.path.split(file_of_exchange_config)
module_name_of_live_config, _ = os.path.splitext(filename_of_live_config)
module_name_of_exchange_config, _ = os.path.splitext(filename_of_exchange_config)

sys.path.append(path_of_live_config)
sys.path.append(path_of_exchange_config)
_config = importlib.import_module(module_name_of_live_config)
_exchange = importlib.import_module(module_name_of_exchange_config)

# ↓↓↓以下需配置↓↓↓
TEST_REPORT = True
RUN_NAME = _config.RUN_NAME
PAGE_LEVERAGE = _config.PAGE_LEVERAGE
MAX_BALANCE = _config.MAX_BALANCE
REAL_LEVERAGE = PAGE_LEVERAGE * MAX_BALANCE
FACTOR_NAME = "TEST"
FACTOR_PARAMS = "PARA01"
# ↑↑↑以上需配置↑↑↑

EXCHANGE_ID = _exchange.EXCHANGE_ID
EXCHANGE_CONFIG = _exchange.EXCHANGE_CONFIG
MIXIN_TOKEN = _exchange.MIXIN_TOKEN
CALLKEY = _exchange.CALLKEY
IMG_TOKEN = _exchange.IMG_TOKEN
SMOOTH_LINE = True
CALL_ALARM = False
REPORT_INTERVAL = "30m"
ROOT_PATH = Path(__file__).resolve().parent
DB_PATH = str(ROOT_PATH / "data/db_files")
LOG_PATH = str(ROOT_PATH / "data/logs")
LOG_LEVEL_CONSOLE = "debug"
LOG_LEVEL_FILE = "debug"


if __name__ == '__main__':
    from my_logger import *
    logger = logging.getLogger("app.sett")
    logger.debug(EXCHANGE_ID)
    logger.debug(RUN_NAME)
