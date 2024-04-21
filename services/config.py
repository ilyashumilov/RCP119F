from enum import Enum
from pydantic import BaseSettings


class BrokerConfig(BaseSettings):
    BROKER_API_KEY: str = ''
    BROKER_API_SECRET: str = ''


class NotifierConfig(BaseSettings):
    NOTIFIER_KEY: str = ''
    NOTIFICATION_CHANNEL_ID: str = ''


class TraderType(str, Enum):
    SHORT_ONLY = 'ShortOnly'
    LONG_ONLY = 'LongOnly'


class PositionType(str, Enum):
    BUY = "Buy"
    SELL = "Sell"


notifier_config = NotifierConfig()
broker_config = BrokerConfig()
