import os
import json
import logging
import requests
from requests.exceptions import Timeout, ConnectionError
import connexion
from apscheduler.schedulers.background import BackgroundScheduler

# Load configuration
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

RECEIVER_URL = config["RECEIVER_URL"]
STORAGE_URL = config["STORAGE_URL"]
PROCESSING_URL = config["PROCESSING_URL"]
ANALYZER_URL = config["ANALYZER_URL"]
TIMEOUT = config["TIMEOUT"]
STATUS_FILE = config["STATUS_FILE"]

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('checkService')

def check_services():
    """Called periodically to check the status of services"""
    status = {
        "receiver": check_service(RECEIVER_URL, "Receiver"),
        "storage": check_service(STORAGE_URL, "Storage"),
        "processing": check_service(PROCESSING_URL, "Processing"),
        "analyzer": check_service(ANALYZER_URL, "Analyzer")
    }

    with open(STATUS_FILE, 'w') as f:
        json.dump(status, f)

def check_service(url, service_name):
    """Helper function to check the status of a service"""
    status = "Unavailable"
    try:
        response = requests.get(url, timeout=TIMEOUT)
        if response.status_code == 200:
            if service_name == "Receiver":
                status = "Healthy"
            else:
                data = response.json()
                status = f"{service_name} has {data['num_bp']} BP and {data['num_hr']} HR events"
            logger.info(f"{service_name} is Healthy")
        else:
            logger.info(f"{service_name} returning non-200 response")
    except (Timeout, ConnectionError):
        logger.info(f"{service_name} is Not Available")
    return status

def get_checks():
    """Endpoint to get the status of services"""
    if os.path.isfile(STATUS_FILE):
        with open(STATUS_FILE, 'r') as f:
            status = json.load(f)
        return status, 200
    else:
        return {"message": "Status file not found"}, 404

# Initialize the Connexion app
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yml")

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(func=check_services, trigger="interval", seconds=10)
scheduler.start()

if __name__ == "__main__":
    app.run(port=8130, host="0.0.0.0")