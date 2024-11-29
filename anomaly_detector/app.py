import connexion
import json
import yaml
import logging
import logging.config
from pykafka import KafkaClient
from threading import Thread
from apscheduler.schedulers.background import BackgroundScheduler
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import os

# Load environment-specific configurations
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

logger.info(f"App Conf File: {app_conf_file}")
logger.info(f"Log Conf File: {log_conf_file}")

# Datastore for anomalies
EVENT_FILE = app_config["datastore"]["filename"]

def save_anomalies(anomalies):
    """Save anomalies to the datastore."""
    with open(EVENT_FILE, 'w') as f:
        json.dump(anomalies, f, indent=2)

def get_anomalies():
    """Process Kafka events and detect anomalies."""
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
                    "event_id": payload["meter_id"],
                    "trace_id": payload["trace_id"],
                    "event_type": event_type,
                    "anomaly_type": "Too High",
                    "description": f"Payment amount {payload['amount']} exceeded $100",
                    "timestamp": payload["timestamp"]
                })

            # Parking anomaly: spots < 0
            elif event_type == "parking_status" and payload["spot_number"] < 0:
                anomalies.append({
                    "event_id": payload["meter_id"],
                    "trace_id": payload["trace_id"],
                    "event_type": event_type,
                    "anomaly_type": "Too Low",
                    "description": f"Parking spot {payload['spots']} is below zero",
                    "timestamp": payload["timestamp"]
                })

        save_anomalies(anomalies)
        logger.info(f"Saved {len(anomalies)} anomalies.")

    except Exception as e:
        logger.error(f"Error processing events: {str(e)}")

# Scheduler initialization
def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(get_anomalies, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/anomalies", strict_validation=True, validate_responses=True)

# Enable CORS if not in test environment
if "TARGET_ENV" not in os.environ or os.environ["TARGET_ENV"] != "test":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8120, host="0.0.0.0")
