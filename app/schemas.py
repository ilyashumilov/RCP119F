from pydantic import BaseModel


class TradeProcessorCreateSchema(BaseModel):
    symbol: str
    type: str
    capital: float
    leverage: float
    upper_bound: float
    lower_bound: float
    grid_count: int

class TaskCancellationRequestSchema(BaseModel):
    celery_task_id: str
