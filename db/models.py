from datetime import datetime
from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class TradeProcess(Base):
    __tablename__ = 'trade_process'
    id = Column(String, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    symbol = Column(String)
    type = Column(String)
    capital = Column(Float)
    leverage = Column(Integer)
    upper_bound = Column(Float)
    lower_bound = Column(Float)
    grid_count = Column(Float)
    unclosed_pnl = Column(Float, default=0.0)
    closed_pnl = Column(Float, default=0.0)
    total_pnl = Column(Float, default=0.0)
    updated_at = Column(DateTime)
    celery_task_id = Column(String)
