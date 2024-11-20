import connexion
from connexion import NoContent
import json
import requests
import datetime
import yaml
import logging
import logging.config
import uuid
from pykafka import KafkaClient
import time


with open('app_conf.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

with open('log_conf.yml', 'r') as f2:
    log_config = yaml.safe_load(f2.read())
    logging.config.dictConfig(log_config)
logger = logging.getLogger('basicLogger')

# connecting kafka
max_retries = 5
retry_count = 0

while retry_count < max_retries:
    try:
        client = KafkaClient(hosts=f"{app_config['events']['hostname']}:{app_config['events']['port']}")
        topic = client.topics[str.encode(app_config['events']['topic'])]
        producer = topic.get_sync_producer()
        logger.info(f"Succesfully connected to Kafka")
        break
    except Exception as e:
        logger.error(f"Failed to connect to Kafka: {e} | Retrying in 5 seconds...")
        time.sleep(5)
        retry_count += 1

def log_data(event, event_type):
    header = {"Content-Type": "application/json"}
    
    trace_id = str(uuid.uuid4())
    event["trace_id"] = trace_id

    logger.info(f'Received event {event_type} request with a trace id of {trace_id}')
    
    msg = {
        "type": event_type,
        "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": event
    }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))
    
    logger.info(f'Returned event {event_type} response (Id: {trace_id}) with status 201')

    return msg_str, 201

def parking_status(body):
    res = log_data(body, "parking_status")
    return NoContent, res[1]

def payment(body):
    res = log_data(body, "payment")
    return NoContent, res[1]

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
