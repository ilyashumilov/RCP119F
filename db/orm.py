from db.models import TradeProcess
from db.config import Session


def create_trade_process(session: Session, **kwargs) -> str:
    instance = TradeProcess(**kwargs)
    session.add(instance)
    session.commit()
    return instance.id


def get_trade_process_by_id(session: Session, process_id: str) -> TradeProcess:
    return session.query(TradeProcess).filter_by(id=process_id).first()


def get_trade_process_by_celery_task_id(session: Session,celery_task_id: str) -> TradeProcess:
    return session.query(TradeProcess).filter_by(celery_task_id=celery_task_id).first()


def get_active_trade_processes(session: Session) -> list[TradeProcess]:
    return session.query(TradeProcess).filter_by(completed_at=None).all()


def update_trade_process(session: Session, process_id: str, **kwargs) -> None:
    trade_process = get_trade_process_by_id(session, process_id)
    if trade_process:
        for key, value in kwargs.items():
            setattr(trade_process, key, value)
        session.commit()
