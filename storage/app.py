import functools
from datetime import datetime
from threading import Thread

import connexion
import json

import sqlalchemy
from connexion import NoContent

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import TemperatureReport, HumidityReport
import logging, logging.config
import yaml

from pykafka import KafkaClient
from pykafka.common import OffsetType


with open ("./storage_config.yml", "r") as f:
    app_config = yaml.safe_load(f)

datastore = app_config["datastore"]
user = datastore["user"]
password = datastore["password"]
hostname = datastore["hostname"]
port = datastore["port"]
database = datastore["db"]

engine = create_engine(
    f"mysql+pymysql://{user}:{password}@{hostname}:{port}/{database}",
    pool_size=20,
    pool_recycle=1800,
    pool_pre_ping=True
)

with open("./log_config.yml", "r") as f:
    LOG_CONFIG = yaml.safe_load(f.read())
    logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger('basicLogger')


def make_session():
    return sessionmaker(bind=engine)()


def use_db_session(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = make_session()
        try:
            return func(session, *args, **kwargs)
        finally:
            session.close()

    return wrapper

@use_db_session
def get_temperatures(session, start_timestamp, end_timestamp):
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)

    statement = sqlalchemy.select(TemperatureReport).where(TemperatureReport.date_created >= start).where(TemperatureReport.date_created < end)
    results = [result.to_dict() for result in session.execute(statement).scalars().all()]

    logger.info("Found %d temperature readings (start: %s, end: %s)", len(results), start, end)

    return results

@use_db_session
def get_humidities(session, start_timestamp, end_timestamp):
    start = datetime.fromisoformat(start_timestamp)
    end = datetime.fromisoformat(end_timestamp)

    statement = sqlalchemy.select(HumidityReport).where(HumidityReport.date_created >= start).where(HumidityReport.date_created < end)
    results = [result.to_dict() for result in session.execute(statement).scalars().all()]

    logger.info("Found %d humidity readings (start: %s, end: %s)", len(results), start, end)

    return results

@use_db_session
def process_messages(session):
    """ Process event messages """
    logger.info("Connecting to Kafka")
    event_hostname = app_config["events"]["hostname"]
    event_port = app_config["events"]["port"]
    hostname = f"{event_hostname}:{event_port}" # localhost:9092
    client = KafkaClient(hosts=hostname)
    topic = client.topics[str.encode(app_config["events"]["topic"])]
    # Create a consume on a consumer group, that only reads new messages
    # (uncommitted messages) when the service re-starts (i.e., it doesn't
    # read all the old messages from the history in the message queue).
    consumer = topic.get_simple_consumer(consumer_group=b'event_group',
    reset_offset_on_start=False,
    auto_offset_reset=OffsetType.LATEST)
    # This is blocking - it will wait for a new message
    for msg in consumer:
        msg_str = msg.value.decode('utf-8')
        msg = json.loads(msg_str)
        logger.info("Message: %s" % msg)
        payload = msg["payload"]
        if msg["type"] == "temperature": # Change this to your event type
            # Store the event1 (i.e., the payload) to the DB
            obj = TemperatureReport(
                device_id=payload["device_id"],
                temperature=payload["temperature"],
                location=payload["location"],
                timestamp=datetime.strptime(payload["timestamp"], "%Y-%m-%dT%H:%M:%S"),
                trace_id=payload["trace_id"]
            )
            session.add(obj)

        elif msg["type"] == "humidity": # Change this to your event type
            # Store the event2 (i.e., the payload) to the DB
            obj = HumidityReport(
                device_id=payload["device_id"],
                humidity=payload["humidity"],
                location=payload["location"],
                timestamp=datetime.strptime(payload["timestamp"], "%Y-%m-%dT%H:%M:%S"),
                trace_id=payload["trace_id"]
            )
            session.add(obj)
        # Commit the new message as being read
        session.commit()
        logger.info("Stored event %s with trace ID %s" % (msg["type"], payload["trace_id"]))

def setup_kafka_thread():
    t1 = Thread(target=process_messages)
    t1.setDaemon(True)
    t1.start()

# Define all required functions
app = connexion.FlaskApp(__name__, specification_dir='')
app.add_api("openapi.yaml", strict_validation=True, validate_responses=True, base_path="/storage")

if __name__ == "__main__":
    setup_kafka_thread()
    app.run(port=8090, host="0.0.0.0")
