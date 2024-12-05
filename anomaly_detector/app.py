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
from connexion import NoContent

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
                    "anomaly_type": "Too Low",
                    "description": f"Parking spot {payload['spot_number']} is below zero",
                    "timestamp": payload["timestamp"]
                })

        if anomalies:
            logger.info(f"Anomalies detected: {anomalies}")
            save_anomalies(anomalies)
            logger.info(f"Saved {len(anomalies)} anomalies.")
            return anomalies, 200  # Return anomalies with HTTP status 200
        else:
            logger.info("No anomalies detected.")
            return NoContent, 204  # Return NoContent with HTTP status 204

    except Exception as e:
        logger.error(f"Error processing events: {e}")
        return {"message": "Internal Server Error"}, 500  # Return error message with HTTP status 500

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
