import time
from datetime import timedelta

from celery import Celery
from pybit import unified_trading

from db.config import Session
from services.config import broker_config
from services.notification_service import notification_service
from services.trade_processor import TradeProcessor

celery = Celery("tasks", broker="redis://redis:6379/0", backend="redis://redis:6379/0")


@celery.task
def trading_task(**kwargs):
    session = Session()
    broker_session = unified_trading.HTTP(
        api_key=broker_config.BROKER_API_KEY,
        api_secret=broker_config.BROKER_API_SECRET,
        testnet=False,
    )

    try:
        processor = TradeProcessor(
            db_session=session, broker_session=broker_session, **kwargs
        )
        processor.perform()
    finally:
        session.close()


@celery.task(bind=True, max_retries=3)
def notify_task(self):
    session = Session()
    try:
        notification_service(session=session)
    except Exception as exc:
        print(exc)
        time.sleep(5)
        raise self.retry(exc=exc)
    finally:
        session.close()


celery.conf.beat_schedule = {
    "notify_task": {
        "task": "tasks.tasks.notify_task",
        "schedule": timedelta(seconds=15),
    },
}
