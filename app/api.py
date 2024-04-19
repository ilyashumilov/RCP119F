import datetime
import uuid

import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import TradeProcessorCreateSchema, TaskCancellationRequestSchema
from tasks.tasks import trading_task
from db.orm import create_trade_process, get_active_trade_processes, get_trade_process_by_celery_task_id, update_trade_process
from db.config import Session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def get_db_session():
    try:
        db_session = Session()
        yield db_session
    finally:
        db_session.close()


@app.get("/stats")
async def get_stats(db_session: Session = Depends(get_db_session)):
    return get_active_trade_processes(db_session)


@app.post("/new")
async def new_process(request_data: TradeProcessorCreateSchema, db_session: Session = Depends(get_db_session)):
    data = request_data.dict()
    trade_process_id = str(uuid.uuid4())
    data.update({'id': trade_process_id})
    task = trading_task.apply_async(kwargs=data)
    data.update({'celery_task_id': task.id})
    create_trade_process(db_session, **data)
    return {'msg': 'Success!'}


@app.post("/cancel")
async def cancel_task(request_data: TaskCancellationRequestSchema, db_session: Session = Depends(get_db_session)):
    target_process_id = get_trade_process_by_celery_task_id(db_session, request_data.celery_task_id).id
    update_trade_process(db_session, target_process_id, completed_at=datetime.datetime.now())
    return {'msg': 'Success!'}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
