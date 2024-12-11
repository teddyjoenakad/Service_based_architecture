import connexion
from connexion import NoContent
import requests
from requests.exceptions import Timeout, ConnectionError
import yaml
import json
import logging
import logging.config
from apscheduler.schedulers.background import BackgroundScheduler
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware
import os

# Environment-specific configuration files
if "TARGET_ENV" in os.environ and os.environ["TARGET_ENV"] == "test":
    print("In Test Environment")
    app_conf_file = "/config/app_conf.yml"
    log_conf_file = "/config/log_conf.yml"
else:
    print("In Dev Environment")
    app_conf_file = "app_conf.yml"
    log_conf_file = "log_conf.yml"

# Load configuration
with open(app_conf_file, 'r') as f:
    app_config = yaml.safe_load(f.read())

with open(log_conf_file, 'r') as f:
    log_config = yaml.safe_load(f.read())
    logging.config.dictConfig(log_config)

logger = logging.getLogger('basicLogger')

# Constants from config
RECEIVER_URL = app_config["services"]["receiver_url"]
STORAGE_URL = app_config["services"]["storage_url"]
PROCESSING_URL = app_config["services"]["processing_url"]
ANALYZER_URL = app_config["services"]["analyzer_url"]
TIMEOUT = app_config["services"]["timeout"]
STATUS_FILE = app_config["services"]["status_file"]

# Ensure status.json exists
if not os.path.isfile(STATUS_FILE):
    logger.info(f"{STATUS_FILE} not found. Creating a new one...")
    with open(STATUS_FILE, 'w') as f:
        json.dump({}, f)

def check_services():
    """Periodically check the status of services and update the status.json file"""
    logger.info("Periodic service check started...")

    status = {}

    # Receiver Service
    receiver_status = "Unavailable"
    try:
        response = requests.get(RECEIVER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            receiver_status = "Healthy"
            logger.info("Receiver is Healthy")
        else:
            logger.info("Receiver returned non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Receiver is Not Available")
    status["receiver"] = receiver_status

    # Storage Service
    storage_status = "Unavailable"
    try:
        response = requests.get(STORAGE_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            storage_json = response.json()
            storage_status = f"Storage has {storage_json['num_parking_events']} parking and {storage_json['num_payment_events']} payment events"
            logger.info("Storage is Healthy")
        else:
            logger.info("Storage returned non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Storage is Not Available")
    status["storage"] = storage_status

    # Processing Service
    processing_status = "Unavailable"
    try:
        response = requests.get(PROCESSING_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            processing_json = response.json()
            processing_status = f"Processing has {processing_json['num_parking_events']} parking and {processing_json['num_payment_events']} payment events"
            logger.info("Processing is Healthy")
        else:
            logger.info("Processing returned non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Processing is Not Available")
    status["processing"] = processing_status

    # Analyzer Service
    analyzer_status = "Unavailable"
    try:
        response = requests.get(ANALYZER_URL, timeout=TIMEOUT)
        if response.status_code == 200:
            analyzer_json = response.json()
            analyzer_status = f"Analyzer has {analyzer_json['parking']} parking and {analyzer_json['payment']} payment events"
            logger.info("Analyzer is Healthy")
        else:
            logger.info("Analyzer returned non-200 response")
    except (Timeout, ConnectionError):
        logger.info("Analyzer is Not Available")
    status["analyzer"] = analyzer_status

    # Write status to file
    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f, indent=2)

    logger.info("Service check completed and status.json updated")
    logger.info("Request received to get service status...")

    if os.path.isfile(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            status = json.load(f)
        return status, 200
    else:
        logger.error("Status file not found")
        return {"message": "Status file not found"}, 404

# Scheduler initialization
def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(check_services, 'interval', seconds=app_config['scheduler']['period_sec'])
    sched.start()

# App setup
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml", base_path="/processing", strict_validation=True, validate_responses=True)

# Disable CORS in the test environment
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
    app.run(port=8130, host="127.0.0.1")