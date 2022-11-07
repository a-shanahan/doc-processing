import logging
import json
from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

consumer = KafkaConsumer(bootstrap_servers='localhost:29092',
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))

consumer.subscribe(['sentiment-ready'])


def start_consumer():
    while True:
        mess = consumer.poll(0.1, max_records=1)
        if len(mess) == 0:
            continue
        try:
            for _, j in mess.items():
                for message in j:
                    logger.info(f'Key: {message.key} Value: {message.value}')
        except NoBrokersAvailable as e:
            logger.debug(f"Error: {e}")
            pass


if __name__ == '__main__':
    start_consumer()
