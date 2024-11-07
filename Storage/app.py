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

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f2:
    log_config = yaml.safe_load(f2.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

user = app_config['datastore']['user']
password = app_config['datastore']['password']
hostname = app_config['datastore']['hostname']
port = app_config['datastore']['port']
db = app_config['datastore']['db']

DB_ENGINE = create_engine(f'mysql+pymysql://{user}:{password}@{hostname}:{port}/{db}')
# print(DB_ENGINE)
Base.metadata.bind = DB_ENGINE
DB_SESSION = sessionmaker(bind=DB_ENGINE)

logger.info(f"connecting to DB. Hostname: {hostname}, Port: {port}")

# =============== Get
def get_parking_status(start_timestamp, end_timestamp):
    """ Gets parking status events between the specified timestamps """
    session = DB_SESSION()
    start_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    readings = session.query(ParkingStatus).filter(
        and_(ParkingStatus.date_created >= start_datetime,
             ParkingStatus.date_created < end_datetime))

    results_list = [reading.to_dict() for reading in readings]
    session.close()

    logger.info(f"Query for parking status events between {start_timestamp} and {end_timestamp} returns {len(results_list)} results")
    return results_list, 200

def get_payment_events(start_timestamp, end_timestamp):
    """ Gets payment events between the specified timestamps """
    session = DB_SESSION()
    start_datetime = datetime.datetime.strptime(start_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    end_datetime = datetime.datetime.strptime(end_timestamp, "%Y-%m-%dT%H:%M:%SZ")
    readings = session.query(PaymentEvent).filter(
        and_(PaymentEvent.date_created >= start_datetime,
             PaymentEvent.date_created < end_datetime))

    results_list = [reading.to_dict() for reading in readings]
    session.close()

    logger.info(f"Query for payment events between {start_timestamp} and {end_timestamp} returns {len(results_list)} results")
    return results_list, 200

# =============== KAFKA
def process_messages():
    """ Process event messages """
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(consumer_group=b'event_group', reset_offset_on_start=False, auto_offset_reset=OffsetType.LATEST)

    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)

        payload = msg["payload"]
        # body = json.loads(payload)

        logger.info(f'Connecting to DB. Hostname: {hostname}, Port: {port}')
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
                session.close()
                logger.debug(f'Stored event parking_status request with a trace id of {payload["trace_id"]}')

            elif msg["type"] == "payment":
                logger.info(f'Connecting to DB. Hostname: {hostname}, Port: {port}')
                session = DB_SESSION()

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
                session.close()
                logger.debug(f'Stored event payment request with a trace id of {payload["trace_id"]}')
        except:
            logger.error("Failed to store event" % msg) 
        finally:
            session.close()
        consumer.commit_offsets()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()
    app.run(port=8090, host="0.0.0.0")