import json
import connexion
import yaml
import logging, logging.config
from pykafka import KafkaClient
import os


with open('./anomaly_detector_config.yml', 'r') as f:
    CONFIG = yaml.safe_load(f.read())

logger = logging.getLogger('basicLogger')

with open("./log_config.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

def update_anomalies():
    logger.info("Received update request in anomaly detector")
    client = KafkaClient(hosts=CONFIG["kafka"]["hostname"])
    topic = client.topics[CONFIG["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    anomaly_counter = 0
    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "humidity":
            if message["payload"]["humidity"] > os.environ["HUMIDITY_MIN"]:
                logger.warning("Humidity anomaly detected!")
                # Add a record to the json file
                anomaly = {
                    "trace_id": message["payload"]["trace_id"],
                    "type": "humidity",
                    "description": "The value detected was: " + str(message["payload"]["humidity"] + "and the threshold limit was: 8"),
                }
                # Overwrite the json file
                with open("anomaly.json", "w") as f:
                    json.dump(anomaly, f)

                # Increase the anomaly counter
                anomaly_counter += 1

        if message["type"] == "temperature":
            if message["payload"]["temperature"] < os.environ["TEMPERATURE_MAX"]:
                logger.warning("Temperature anomaly detected!")
                # Add a record to the json file
                anomaly = {
                    "trace_id": message["payload"]["trace_id"],
                    "type": "temperature",
                    "description": "The value detected was: " + str(message["payload"]["temperature"] + "and the threshold limit was: 5"),
                }
                # Overwrite the json file
                with open("anomaly.json", "w") as f:
                    json.dump(anomaly, f)

                # Increase the anomaly counter
                anomaly_counter += 1

    logger.info(f"Anomalies detected: {anomaly_counter}")
    return {"anomalies_count": anomaly_counter}, 200

def get_anomalies(event_type=None):
    logger.info("Received anomaly request in anomaly detector")
    # If the provided event_type is invalid, return a 400 error
    if event_type not in ["humidity", "temperature", None]:
        return {"message": "Invalid event type!"}, 400

    if event_type == "humidity":
        with open("anomaly.json", "r") as f:
            anomaly = json.load(f)
            if anomaly["type"] == "humidity":
                return anomaly, 200
            else:
                return {"message": "No humidity anomalies detected!"}, 404
    elif event_type == "temperature":
        with open("anomaly.json", "r") as f:
            anomaly = json.load(f)
            if anomaly["type"] == "temperature":
                return anomaly, 200
            else:
                return {"message": "No temperature anomalies detected!"}, 404
    else:
        with open("anomaly.json", "r") as f:
            anomaly = json.load(f)
            return anomaly, 200


# Define all required functions
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("anomaly.yaml", strict_validation=True, validate_responses=True, base_path="/anomaly_detector")

if __name__ == "__main__":
    app.run(port=8120, host="0.0.0.0")
