import logging
from fastapi import FastAPI, HTTPException, Depends
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from service import staging_srvc
from utils.db import get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()
scheduler = AsyncIOScheduler()

@app.on_event("startup")
async def startup():
    scheduler.start()
    logger.info("Scheduler arrancado")

@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()
    logger.info("Scheduler parado")

@app.post("/staging/start/{client_id}")
async def start_staging(client_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await staging_srvc.iniciar_staging(scheduler, client_id, session)
        return {"status": "Staging iniciado"}
    except Exception as e:
        logger.error(f"Error iniciando staging para cliente {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Error iniciando staging")

@app.post("/staging/stop/{client_id}")
async def stop_staging(client_id: int, session: AsyncSession = Depends(get_session)):
    try:
        await staging_srvc.apagar_staging(scheduler, client_id, session)
        return {"status": "Staging detenido"}
    except Exception as e:
        logger.error(f"Error deteniendo staging para cliente {client_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deteniendo staging")
