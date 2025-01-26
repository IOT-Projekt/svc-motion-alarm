from kafka_handler import (
    KafkaConfig,
    setup_kafka_consumer
)
import requests
import logging
import os
import datetime
import json

# setup logging
logging.basicConfig(level=logging.INFO)

# Get constants from environment variables
KAFKA_MOTION_TOPIC = os.getenv("KAFKA_MOTION_TOPIC", "motion")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", None)
MOTION_ALARM_STR = os.getenv("MOTION_ALARM_STR", "MOTION DETECTED")

def send_motion_alarm() -> None:
    """Send a motion alarm to Discord."""
    # check if the Discord webhook URL is set
    if not DISCORD_WEBHOOK_URL:
        logging.error("Discord webhook URL is not set.")
        return
    
    # create payload and sent it to Discord
    payload = {"content": MOTION_ALARM_STR}
    response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    
    # log whether the motion alarm was sent successfully
    if response.status_code == 204:
        logging.info("Motion alarm sent to Discord.")
    else:
        logging.error(f"Failed to send motion alarm to Discord. Status code: {response.status_code}")


def check_if_motion_alarm(timestamp: float) -> bool:
    """Check if a motion alarm should be sent. If the timestamp is after 8pm and before 6am, send the motion alarm"""
    # check if the motion alarm string is set
    if not MOTION_ALARM_STR:
        logging.error("Motion alarm string is not set.")
        return False
    
    # convert the timestamp to a datetime object
    dt = datetime.datetime.fromtimestamp(timestamp)
    
    # check if the time is between 8pm and 6am
    if dt.hour >= 20 or dt.hour < 6:
        return True

def extract_data(message) -> tuple:
    # Get the json string and format it to json
    message = message.value["message"]
    json_message = json.loads(message)
    
    # get the data from the json message
    timestamp = json_message["timestamp"]
    motion_detected = json_message["motion_detected"]
    return timestamp,motion_detected
            

def main() -> None:
    # set up Kafka consumer
    kafka_config = KafkaConfig()
    consumer = setup_kafka_consumer(kafka_config, [KAFKA_MOTION_TOPIC])

    for message in consumer:
        # log the received message
        logging.info(f"Received message: {message.topic} -> {message.value}")

        # get the data from the message
        timestamp, motion_detected = extract_data(message)
        
        # check if a motion alarm should be sent
        if motion_detected and check_if_motion_alarm(timestamp):
            send_motion_alarm()


if __name__ == "__main__":
    main()