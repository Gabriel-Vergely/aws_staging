import logging
import os

import boto3
from botocore.exceptions import ClientError, BotoCoreError

AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
LOGGER = logging.getLogger(__name__)

ec2 = boto3.client("ec2", region_name=AWS_REGION)

def instance_state(ec2_id):
    try:
        resp = ec2.describe_instances(InstanceIds=[ec2_id])
        return resp["Reservations"][0]["Instances"][0]["State"]["Name"]
    except (ClientError, BotoCoreError) as exc:
        LOGGER.error("describe_instances fallo: %s", exc)
        return "unknown"

def start_instance(ec2_id):
    try:
        ec2.start_instances(InstanceIds=[ec2_id])
        LOGGER.info("start_instances %s enviado", ec2_id)
    except (ClientError, BotoCoreError) as exc:
        LOGGER.error("start_instances fallo: %s", exc)

def stop_instance(ec2_id):
    try:
        ec2.stop_instances(InstanceIds=[ec2_id])
        LOGGER.info("stop_instances %s enviado", ec2_id)
    except (ClientError, BotoCoreError) as exc:
        LOGGER.error("stop_instances fallo: %s", exc)
