import datetime
import json
import time
import connexion
from connexion import NoContent
import yaml
import logging, logging.config
from pykafka import KafkaClient


with open('..config/receiver_config.yml', 'r') as f:
    app_config = yaml.safe_load(f.read())

logger = logging.getLogger('basicLogger')

with open("..config/log_conf.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

def post_api_weather_temperature(body):
    # Add a trace_id to the event
    trace_id = time.time_ns()

    # Log the event
    logger.info("Received event temperature report with trace ID %s", trace_id)

    # Add the trace_id to the body
    body["trace_id"] = trace_id

    hostname = app_config["events"]["hostname"]
    port = app_config["events"]["port"]
    topic = app_config["events"]["topic"]

    client = KafkaClient(hosts=f'{hostname}:{port}')
    topic = client.topics[str.encode(f'{topic}')]
    producer = topic.get_sync_producer()
    msg = {"type": "temperature",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body
           }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    return NoContent, 201


def post_api_weather_humidity(body):
    # Add a trace_id to the event
    trace_id = time.time_ns()

    # Log the event
    logger.info("Received event humidity report with trace ID %s", trace_id)

    # Add the trace_id to the body
    body["trace_id"] = trace_id

    hostname = app_config["events"]["hostname"]
    port = app_config["events"]["port"]
    topic = app_config["events"]["topic"]

    client = KafkaClient(hosts=f'{hostname}:{port}')
    topic = client.topics[str.encode(f'{topic}')]
    producer = topic.get_sync_producer()
    msg = {"type": "humidity",
           "datetime": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
           "payload": body
           }
    msg_str = json.dumps(msg)
    producer.produce(msg_str.encode('utf-8'))

    return NoContent, 201

# Define all required functions
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True)

if __name__ == "__main__":
    app.run(port=8080, host="0.0.0.0")
