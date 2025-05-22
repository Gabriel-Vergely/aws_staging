from datetime import datetime, timedelta
import logging
import threading
import time

from api import aws_boto3
from utils.db import fetch_active_clients, queue_task

IDLE_TIMEOUT_MINUTES = 15

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

def run_staging_service(stop_event):
    logging.info("StagingService iniciado")
    while not stop_event.is_set():
        try:
            cycle_once()
        except Exception as exc:
            logging.exception("Error ciclo principal: %s", exc)
        time.sleep(60)

def cycle_once():
    now = datetime.utcnow()
    for client in fetch_active_clients():
        state = client["state"]
        last_activity = client["last_activity"]
        if state == "on":
            if last_activity and (now - last_activity) > timedelta(minutes=IDLE_TIMEOUT_MINUTES):
                logging.info("Cliente %s inactivo > %d min; apagando.", client["id"], IDLE_TIMEOUT_MINUTES)
                queue_task("stop", client["id"], client["ec2_id"])

