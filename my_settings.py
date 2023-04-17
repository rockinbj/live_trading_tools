import sys
import os
import importlib


# ↓↓↓以下需配置↓↓↓
# 实盘config文件的绝对路径
file_of_live_config = r"D:\Code\alpha_v7.0.5\src_product\config.py"
# 实盘交易所文件的绝对路径
file_of_exchange_config = r"D:\Code\alpha_v7.0.5\src_product\exchangeConfig.py"
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
FACTOR_NAME = _config.strategy_list[0]["factors"]
FACTOR_PARAMS = _config.strategy_list[0]["hold_period"]
# ↑↑↑以上需配置↑↑↑

EXCHANGE_ID = _exchange.EXCHANGE_ID
EXCHANGE_CONFIG = _exchange.EXCHANGE_CONFIG
MIXIN_TOKEN = _exchange.MIXIN_TOKEN
CALLKEY = _exchange.CALLKEY
IMG_TOKEN = _exchange.IMG_TOKEN
SMOOTH_LINE = True
CALL_ALARM = False
REPORT_INTERVAL = "30m"
DB_PATH = "data/db_files"
LOG_PATH = "data/logs"
LOG_LEVEL_CONSOLE = "debug"
LOG_LEVEL_FILE = "debug"


if __name__ == '__main__':
    from my_logger import *
    logger = logging.getLogger("app.sett")
    logger.debug(EXCHANGE_ID)
    logger.debug(RUN_NAME)
