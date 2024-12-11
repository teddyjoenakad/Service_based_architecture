import connexion
from connexion import NoContent
from sqlalchemy import and_, create_engine
from sqlalchemy.orm import sessionmaker
from base import Base
from parking_status import ParkingStatus
from payment import PaymentEvent
import datetime
import pymysql
import yaml
import logging
import logging.config
import json
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
import time
import os

if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f2:
    log_config = yaml.safe_load(f2.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

logger.info("App Conf File: %s" % app_conf_file)
logger.info("Log Conf File: %s" % log_conf_file)

user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

DB_ENGINE = create_engine(f'mysql+pymysql://{user}:{password}@{hostname}:{port}/{db}', pool_size=0, pool_recycle=-1, pool_pre_ping=True)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(f"connecting to DB. Hostname: {hostname}, Port: {port}")

def save_anomalies(anomalies):
    data_file = '/data/data.json'
    if not os.path.exists('/data'):
        os.makedirs('/data')
    if not os.path.exists(data_file):
        with open(data_file, 'w') as f:
            json.dump([], f)

    with open(data_file, 'r+') as f:
        data = json.load(f)
        data.extend(anomalies)
        f.seek(0)
        json.dump(data, f)

def get_anomalies():
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)

    logger.info("Processing events for anomalies.")
    anomalies = []

    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            event_type = msg["type"]
            payload = msg["payload"]

            # Payment anomaly: amount > 100
            if event_type == "payment" and payload["amount"] > 100:
                anomalies.append({
                    "event_id": str(payload["meter_id"]),
                    "trace_id": payload["trace_id"],
                    "event_type": event_type,
                    "anomaly_type": "Too High",
                    "description": f"Payment amount {payload['amount']} exceeded $100",
                    "timestamp": payload["timestamp"]
                })

            # Parking anomaly: spots < 0
            elif event_type == "parking_status" and payload["spot_number"] < 0:
                anomalies.append({
                    "event_id": str(payload["meter_id"]),
                    "trace_id": payload["trace_id"],
                    "event_type": event_type,
                    "anomaly_type": "Invalid Spot Number",
                    "description": f"Spot number {payload['spot_number']} is less than 0",
                    "timestamp": payload["timestamp"]
                })
    except Exception as e:
        logger.error(f"Error processing messages: {str(e)}")

    save_anomalies(anomalies)
    return anomalies, 200

def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])

    max_retries = 5
    retry_count = 0

    while retry_count < max_retries:
        try:
            client = KafkaClient(hosts=hostname)
            topic = client.topics[str.encode(app_config["events"]["topic"])]
            logger.info(f"Succesfully connected to Kafka")
            break
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e} | Retrying in 10 seconds...")
            time.sleep(5)
            retry_count += 1        

    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False, auto_offset_reset=OffsetType.LATEST)

    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)

        payload = msg["payload"]
        session = DB_SESSION()
        try:
            if msg["type"] == "parking_status":
                ps = ParkingStatus(
                    meter_id=payload['meter_id'],
                    device_id=payload['device_id'],
                    status=payload['status'],
                    spot_number=payload['spot_number'],
                    timestamp=payload['timestamp'],
                    trace_id=payload['trace_id']
                )
                session.add(ps)
                session.commit()
                logger.debug(f'Stored event parking_status request with a trace id of {payload["trace_id"]}')

            elif msg["type"] == "payment":
                pm = PaymentEvent(
                    meter_id=payload['meter_id'],
                    device_id=payload['device_id'],
                    amount=payload['amount'],
                    duration=payload['duration'],
                    timestamp=payload['timestamp'],
                    trace_id=payload['trace_id']
                )
                session.add(pm)
                session.commit()
                logger.debug(f'Stored event payment request with a trace id of {payload["trace_id"]}')
        except Exception as e:
            logger.error(f"Failed to store event: {str(e)}")
        finally:
            session.close()
        consumer.commit_offsets()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/storage", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, host="0.0.0.0")