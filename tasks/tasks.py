from celery import Celery
from services.trade_processor import TradeProcessor
from services.notification_service import notification_service
from datetime import timedelta
from db.config import Session

celery = Celery(
    "tasks",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0"
)


@celery.task
def trading_task(**kwargs):
    session = Session()
    try:
        processor = TradeProcessor(db_session=session, **kwargs)
        processor.perform()
    finally:
        session.close()

@celery.task
def notify_task():
    session = Session()
    try:
        notification_service(session)
    except:
        pass
    finally:
        session.close()


celery.conf.beat_schedule = {
    'notify_task': {
        'task': 'tasks.tasks.notify_task',
        'schedule': timedelta(minutes=15),
    },
}
