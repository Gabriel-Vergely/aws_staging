import logging
from datetime import datetime, timedelta
from threading import Thread

from api import aws_boto3
from model.client_model import Cliente, EstadoCliente
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound

logger = logging.getLogger(__name__)

def apagar_ec2_async(ec2_id: str):
    def target():
        logger.info(f"Apagando EC2 {ec2_id} en hilo separado")
        aws_boto3.stop_instance(ec2_id)
    Thread(target=target).start()

def arrancar_ec2_async(ec2_id: str):
    def target():
        logger.info(f"Arrancando EC2 {ec2_id} en hilo separado")
        aws_boto3.start_instance(ec2_id)
    Thread(target=target).start()

async def programar_apagado(scheduler, client: Cliente):
    job_id = f"apagado_{client.id}"

    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job apagado anterior {job_id} cancelado")
    except Exception:
        pass

    scheduler.add_job(
        apagar_ec2_async,
        'date',
        run_date=client.fecha_apagado,
        args=[client.ec2_id],
        id=job_id,
        misfire_grace_time=300
    )
    logger.info(f"Job apagado {job_id} programado para {client.fecha_apagado}")

async def iniciar_staging(scheduler, client_id: int, session):
    try:
        result = await session.execute(select(Cliente).filter(Cliente.id == client_id))
        client = result.scalar_one()
    except NoResultFound:
        logger.error(f"No existe cliente con id {client_id}")
        return

    if client.state == EstadoCliente.on:
        logger.info(f"Cliente {client_id} ya tiene staging activo")
        return

    if client.horas_restantes <= 0:
        logger.warning(f"Cliente {client_id} no tiene horas restantes para usar")
        return

    ahora = datetime.utcnow()

    arrancar_ec2_async(client.ec2_id)

    client.hora_inicio = ahora
    client.fecha_apagado = ahora + timedelta(hours=client.horas_restantes)
    client.state = EstadoCliente.on

    await session.commit()

    await programar_apagado(scheduler, client)

async def apagar_staging(scheduler, client_id: int, session):
    try:
        result = await session.execute(select(Cliente).filter(Cliente.id == client_id))
        client = result.scalar_one()
    except NoResultFound:
        logger.error(f"No existe cliente con id {client_id}")
        return

    if client.state == EstadoCliente.off:
        logger.info(f"Cliente {client_id} ya tiene staging apagado")
        return

    apagar_ec2_async(client.ec2_id)

    job_id = f"apagado_{client.id}"
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job apagado {job_id} cancelado tras apagado manual")
    except Exception:
        pass

    ahora = datetime.utcnow()
    tiempo_usado = (ahora - client.hora_inicio).total_seconds() / 3600
    horas_restantes = max(client.horas_restantes - tiempo_usado, 0)

    client.state = EstadoCliente.off
    client.hora_inicio = None
    client.fecha_apagado = None
    client.horas_restantes = horas_restantes

    await session.commit()
