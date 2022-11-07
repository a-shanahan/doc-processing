"""
This script monitors the 'new-document' Kafka topic for uploaded files that need to be processed. The
uploaded files have been stored in a directory and the filename is passed to the Layout Parser model
for text extraction. The results are stored in ElasticSearch and a notification is sent to the
'processed-document' topic containing the ElasticSearch UIDs.
"""
import logging
from utils import *
import json
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import NoBrokersAvailable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# ElasticSearch index name to store results
index_name = 'document-index'

parser = initialise_model()
logger.info('Model loaded...connecting to Elastic Search')

es_connect = attempt_es(index_name)

# Kafka connection details. URL name is docker name
producer = KafkaProducer(bootstrap_servers='kafka:9092', api_version=(0, 10, 1))
consumer = KafkaConsumer(bootstrap_servers='kafka:9092',
                         api_version=(0, 10, 1),
                         value_deserializer=lambda m: json.loads(m.decode('utf-8')))

consumer.subscribe(['new-document'])

# Layout Parser reads the file from the filesystem. This is mapped as a docker volume
upload_folder = '/file_storage'


def start_consumer():
    while True:
        kafka_message = consumer.poll(5)
        if len(kafka_message) == 0:
            continue
        try:
            for key, value in kafka_message.items():
                message = value[0]
                msg = message.value
                # Send file details to parser and upload to ES
                results, ids = parse_layout(msg.get('docId'), es_connect, index_name,
                                            parser, msg.get('filename'), upload_folder)
                logger.info(f'Results: {results}')
                logger.info(f'Elastic Search metadata: {results}')
                msg_processed = json.dumps({'docId': msg.get('docId')}).encode('utf-8')
                ack = producer.send('processed-document', msg_processed)
                _ = ack.get()
                logger.info('New Elastic Ids..', ids)
        except (AttributeError, NoBrokersAvailable) as e:
            logger.debug(f'Error: {e}')
            pass


if __name__ == '__main__':
    start_consumer()
