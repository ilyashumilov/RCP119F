import datetime
from enum import Enum
from typing import Optional

from pybit import unified_trading
from pydantic import BaseSettings

mode = "test"

api_key_mainnet = ""
api_secret_mainnet = ""

api_key_testnet = "nXdiK5s2tns9pfPDMU"
api_secret_testnet = "8MGUCrkhHRZPSyuvoiYk6yX1AygAHTGcBHaf"

api_key = api_key_testnet if mode == "test" else api_key_mainnet
api_secret = api_secret_testnet if mode == "test" else api_secret_mainnet

session = unified_trading.HTTP(api_key=api_key, api_secret=api_secret, testnet=False)

timeframe = {
    "start": datetime.datetime(2023, 11, 10, 11, 00, 00),
    "end": datetime.datetime(2023, 11, 21, 11, 00, 00),
    "interval": 15,
}


class NotifierConfig(BaseSettings):
    NOTIFIER_KEY: Optional[str] = "6730780586:AAG_Bw7Wz_hvqWC-IVw1AlKUBIqJk7FmtWY"
    LISTENER_KEY: Optional[str] = "7124927214:AAFcwuyZarmxa5S15qTd_XtCXwbMjvxol3U"
    NOTIFICATION_CHANNEL_ID: Optional[str] = "-1002018425245"


notifier_config = NotifierConfig()
K_FOLD_N_SPLITS = 1

class TraderType(str, Enum):
    SHORT_ONLY = 'ShortOnly'
    LONG_ONLY = 'LongOnly'


class PositionType(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


class OrderStatus(str, Enum):
    NEW = 'new'
    PENDING_CLOSE = 'pending_close'
    CLOSED = 'closed'
