import json
import logging.config
from datetime import datetime, timedelta

import connexion
import httpx
import yaml
from apscheduler.schedulers.background import BackgroundScheduler
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

with open('./processing_config.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

logger = logging.getLogger('basicLogger')

with open("./log_config.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

def populate_stats():
    # Log an info message indicating the start of the periodic processing
    logger.info("Periodic processing has started")

    # Default stats, last_updated will be set to yesterday
    stats = {
        "num_temperature_readings": 0,
        "num_humidity_readings": 0,
        "max_temperature": float('-inf'),
        "max_humidity": float('-inf'),
        "last_updated": (datetime.now() - timedelta(days=1)).isoformat()
    }

    # Read current stats from JSON file
    try:
        with open(app_config["datastore"]["filename"], 'r') as f:
            stats = json.load(f)
    except FileNotFoundError:
        logger.info("JSON Data store not found. Using default values.")

    current_time = datetime.now().isoformat()
    # Print the current time
    logger.info(f"The current time is: {current_time}")
    # Get the last updated timestamp
    last_updated_str = stats.get("last_updated", (datetime.now() - timedelta(days=1)).isoformat())
    start_timestamp = last_updated_str
    end_timestamp = current_time

    # Query the storage service
    try:
        temp_url = app_config['eventstores']['temperature']['url']
        humidity_url = app_config['eventstores']['humidity']['url']
        response_temp = httpx.get(f"{temp_url}?start_timestamp={start_timestamp}&end_timestamp={end_timestamp}")
        response_humidity = httpx.get(f"{humidity_url}?start_timestamp={start_timestamp}&end_timestamp={end_timestamp}")

        if response_temp.status_code != 200:
            logger.error(f"Failed to get temperature data: {response_temp.status_code}")
            return
        if response_humidity.status_code != 200:
            logger.error(f"Failed to get humidity data: {response_humidity.status_code}")
            return

        temp_data = response_temp.json()
        humidity_data = response_humidity.json()

        logger.info(f"Received {len(temp_data)} temperature events")
        logger.info(f"Received {len(humidity_data)} humidity events")

        # Update stats
        stats["num_temperature_readings"] += len(temp_data)
        stats["num_humidity_readings"] += len(humidity_data)

        if temp_data:
            stats["max_temperature"] = max(event["temperature"] for event in temp_data)
        else:
            stats["max_temperature"] = 0

        if humidity_data:
            stats["max_humidity"] = max(event["humidity"] for event in humidity_data)
        else:
            stats["max_humidity"] = 0


        stats["last_updated"] = current_time

        # Write updated stats to JSON file
        with open('stats.json', 'w') as f:
            json.dump(stats, f)

        logger.debug(f"Updated stats: {stats}")
        logger.info("Periodic processing has ended")

    except Exception as e:
        logger.error(f"Error during processing: {e}")


def init_scheduler():
    sched = BackgroundScheduler(daemon=True)
    sched.add_job(populate_stats,
    'interval',
    seconds=app_config['scheduler']['interval'])
    sched.start()

def get_stats():
    logger.info("GET /stats request received")

    try:
        with open('stats.json', 'r') as f:
            stats = json.load(f)
    except FileNotFoundError:
        logger.error("stats.json not found. Statistics do not exist")
        return {"message": "Statistics do not exist"}, 404

    logger.debug(f"Statistics: {stats}")
    logger.info("GET /stats request completed")
    return stats, 200


# Define all required functions
app = connexion.FlaskApp(__name__, specification_dir='')

app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    init_scheduler()
    app.run(port=8100, host="0.0.0.0")
