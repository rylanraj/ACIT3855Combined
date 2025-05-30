import logging, logging.config
import os

import connexion
import json
import yaml
from pykafka import KafkaClient
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware


with open('./analyzer_config.yml', 'r') as f:
    CONFIG = yaml.safe_load(f.read())

logger = logging.getLogger('basicLogger')

with open("./log_config.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

def get_temperature(index):
    client = KafkaClient(hosts=CONFIG["kafka"]["hostname"])
    topic = client.topics[CONFIG["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "temperature":
            if counter == index:
                return message["payload"], 200

            counter += 1

    return {"message": f"No message at index {index}!"}, 404

def get_humidity(index):
    client = KafkaClient(hosts=CONFIG["kafka"]["hostname"])
    topic = client.topics[CONFIG["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    counter = 0
    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "humidity":
            if counter == index:
                return message["payload"], 200

            counter += 1

    return {"message": f"No message at index {index}!"}, 404

def get_stats():
    client = KafkaClient(hosts=CONFIG["kafka"]["hostname"])
    topic = client.topics[CONFIG["kafka"]["topic"].encode()]
    consumer = topic.get_simple_consumer(reset_offset_on_start=True, consumer_timeout_ms=1000)
    temperature_count = 0
    humidity_count = 0
    for msg in consumer:
        message = json.loads(msg.value.decode("utf-8"))
        if message["type"] == "temperature":
            temperature_count += 1
        elif message["type"] == "humidity":
            humidity_count += 1

    return {"temperature_count": temperature_count, "humidity_count": humidity_count}, 200

# Define all required functions
app = connexion.FlaskApp(__name__, specification_dir='')

if "CORS_ALLOW_ALL" in os.environ and os.environ["CORS_ALLOW_ALL"] == "yes":
    app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.add_api("openapi.yaml", strict_validation=True, validate_responses=True, base_path="/analyzer")

if __name__ == "__main__":
    app.run(port=8110, host="0.0.0.0")