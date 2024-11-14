import connexion
from connexion import NoContent
import json
import yaml
import logging
import logging.config
from pykafka import KafkaClient
from pykafka.common import OffsetType
from threading import Thread
from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f2:
    log_config = yaml.safe_load(f2.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

def get_parking_status(index):
    """Get Parking Status Event in History"""
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    
    logger.info("Retrieving parking status event at index %d" % index)

    list_of_events = []
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            
            if msg['type'] == 'parking_status':
                list_of_events.append(msg["payload"])
            
        payload = list_of_events[index]
        return payload, 200
    except:
        logger.error("No more messages found")
    logger.error("Could not find parking status event at index %d" % index)
    return {"message": "Not Found"}, 404

def get_payment_events(index):
    """Get Payment Event in History"""
    hostname = "%s:%d" % (app_config["events"]["hostname"], app_config["events"]["port"])
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    logger.info("Retrieving payment event at index %d" % index)

    list_of_events = []
    try:
        for msg in consumer:
            msg_str = msg.value.decode('utf-8')
            msg = json.loads(msg_str)
            
            if msg['type'] == 'payment':
                list_of_events.append(msg["payload"])
            
        payload = list_of_events[index]
        return payload, 200
    except:
        logger.error("No more messages found")
    logger.error("Could not find payment event at index %d" % index)
    return {"message": "Not Found"}, 404

def get_event_stats():
    """Get Event Stats"""
    hostname = f"{app_config['events']['hostname']}:{app_config['events']['port']}"
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]

    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    num_parking_events = 0
    num_payment_events = 0

    try:
        for msg in consumer:
            msg_str = msg.value.decode("utf-8")
            msg = json.loads(msg_str)
            if msg["type"] == "parking_status":
                num_parking_events += 1
            elif msg["type"] == "payment":
                num_payment_events += 1
        return {"num_parking_events": num_parking_events, "num_payment_events": num_payment_events}, 200
    except Exception as e:
        logger.error("Error retrieving event stats: %s", str(e))
    return {"message": "Error retrieving stats"}, 500


app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

# with app.app_context():

app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")