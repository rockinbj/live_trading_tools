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
module_name_of_live_config, _ = os.path.splitext(filename_of_live_config)

sys.path.append(path_of_live_config)
_config = importlib.import_module(module_name_of_live_config)

# ↓↓↓以下需配置↓↓↓
TEST_REPORT = True
RUN_NAME = _config.RUN_NAME
PAGE_LEVERAGE = _config.PAGE_LEVERAGE
MAX_BALANCE = _config.MAX_BALANCE
# ↑↑↑以上需配置↑↑↑

EXCHANGE_ID = _config.EXCHANGE_ID
EXCHANGE_CONFIG = _config.EXCHANGE_CONFIG
MIXIN_TOKEN = _config.MIXIN_TOKEN
CALLKEY = _config.CALLKEY
SMMS_TOKEN = _config.SMMS_TOKEN
CALL_ALARM = _config.CALL_ALARM
REPORT_INTERVAL = _config.REPORT_INTERVAL
LOG_PATH = "data/logs"
LOG_LEVEL_CONSOLE = "debug"
LOG_LEVEL_FILE = "debug"
DB_PATH = "data/db_files"
