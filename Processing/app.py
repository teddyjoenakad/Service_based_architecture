import connexion
from connexion import NoContent
import json
import requests
import datetime
import yaml
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
import os.path
from collections import Counter
from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
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

EVENT_FILE = app_config["datastore"]["filename"]

def populate_stats():
    """ Periodically update stats """
    logger.info("Periodic processing started...")

    # Read current JSON
    if os.path.isfile(EVENT_FILE):
        with open(EVENT_FILE, 'r') as f3:
            stats = json.load(f3)
    else:
        logger.info(f"{EVENT_FILE} not found. Creating a new one...")
        with open(EVENT_FILE, 'w') as f:
            json.dump({'total_status_events': 0, 
                       'total_payment_events': 0, 
                       'most_frequent_meter': None,
                       'highest_payment': 0, 
                       'last_updated': '2024-01-01T23:59:59Z'
                       }, f)


    # Get current datetime
    received_timestamp = stats["last_updated"]
    current_timestamp = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
    headers = {'accept': 'application/json'}
    parameters = {
        'start_timestamp': received_timestamp,
        'end_timestamp': current_timestamp
        }

    # Query parking status events
    URL_PARKING = app_config["eventstore"]["parking"]
    response_parking = requests.get(URL_PARKING, headers=headers, params=parameters)

    if response_parking.status_code != 200:
        logger.error(f"Failed to fetch parking status events: {response_parking.status_code}")
    else:
        parking_data = response_parking.json()
        num_parking_events = len(parking_data)
        logger.info(f"Fetched parking status events: {response_parking.json()}")
        logger.info(f"Fetched {num_parking_events} parking status events.")

        # Update stats based on parking events
        stats['total_status_events'] += num_parking_events
        if parking_data:
            meters = [entry['meter_id'] for entry in parking_data]
            stats['most_frequent_meter'] = Counter(meters).most_common(1)[0][0]

    # Query payment events
    URL_PAYMENT = app_config["eventstore"]["payment"]
    response_payment = requests.get(URL_PAYMENT, headers=headers, params=parameters)

    if response_payment.status_code != 200:
        logger.error(f"Failed to fetch payment events: {response_payment.status_code}")
    else:
        payment_data = response_payment.json()
        num_payment_events = len(payment_data)
        # logger.info(f"Fetched payment status events: {response_payment.json()}")
        # logger.info(f"Fetched {num_payment_events} payment events.")

        # Update stats based on payment events
        stats['total_payment_events'] += num_payment_events
        if payment_data:
            highest_payment = max(entry['amount'] for entry in payment_data)
            stats['highest_payment'] = max(stats['highest_payment'], highest_payment)

    # Update last_updated timestamp
    stats['last_updated'] = current_timestamp

    # Write updated stats back to the JSON file
    with open(EVENT_FILE, 'w') as file:
        json.dump(stats, file, indent=2)

    logger.debug(stats)
    logger.info("Periodic processing complete...")

def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

# Your functions here
def get_stats():  # /parking/stats
    logger.info("===> Request for stats started...")
    if os.path.isfile(EVENT_FILE):
        with open(EVENT_FILE, 'r') as f4:
            statsread = json.load(f4)
    else:
        logger.error(f"Stats file {EVENT_FILE} cannot be found")
        return {"message": "Statistics do not exist"}, 404

    logger.debug(statsread)
    logger.info("===> Request for stats complete...")
    
    return statsread, 200

app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", strict_validation=True, validate_responses=True)

#app = FlaskApp(__name__)

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
    app.run(port=8100, host="0.0.0.0")
