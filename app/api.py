import datetime
import uuid

import uvicorn
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse

from app.schemas import (OverviewerRequestSchema,
                         TaskCancellationRequestSchema,
                         TradeProcessorCreateSchema)
from db.config import Session
from db.orm import (create_trade_process, get_active_trade_processes,
                    get_trade_process_by_celery_task_id, update_trade_process)
from services.data_gainer_service import get_tradeable_symbols
from services.notification_service import notification_service
from services.overview_service import Overviewer
from tasks.tasks import trading_task
from fastapi.staticfiles import StaticFiles

c_index = -1
symbols = get_tradeable_symbols()
symbols = [s for s in symbols if "-" not in s]

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
async def new_process(
    request_data: TradeProcessorCreateSchema,
    db_session: Session = Depends(get_db_session),
):
    data = request_data.dict()
    trade_process_id = str(uuid.uuid4())
    data.update({"id": trade_process_id})
    task = trading_task.apply_async(kwargs=data)
    data.update({"celery_task_id": task.id})
    create_trade_process(db_session, **data)
    return {"msg": "Success!"}


@app.post("/cancel")
async def cancel_task(
    request_data: TaskCancellationRequestSchema,
    db_session: Session = Depends(get_db_session),
):
    target_process_id = get_trade_process_by_celery_task_id(
        db_session, request_data.celery_task_id
    ).id
    update_trade_process(
        db_session, target_process_id, completed_at=datetime.datetime.now()
    )
    return {"msg": "Success!"}


@app.get("/")
async def index():
    global c_index
    c_index = -1

    with open("templates/index.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.get("/calculator")
async def calculator():
    with open("templates/calculator.html", "r") as file:
        html_content = file.read()
    return HTMLResponse(content=html_content)


@app.post("/get_new_data")
async def get_new_data(request_data: OverviewerRequestSchema):
    payload_c_index = request_data.c_index

    global c_index
    if payload_c_index != "":
        c_index = int(payload_c_index)
    else:
        c_index += 1

    overviewer = Overviewer(symbols[c_index])
    new_chart_html = await overviewer.process()

    return {
        "new_chart_json": new_chart_html.to_json(),
        "c_index": c_index,
    }


@app.post("/notify")
async def notify_enpoint(request_data: OverviewerRequestSchema):
    current_c_index = int(request_data.c_index)
    notification_service(context=symbols[current_c_index])
    return "null"


@app.get("/favicon.ico")
async def get_favicon():
    return FileResponse("statics/favicon.png") # noqa


app.mount("/statics", StaticFiles(directory="/app/statics"), name="static")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
