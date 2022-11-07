import json
import uuid
from kafka import KafkaProducer

producer = KafkaProducer(bootstrap_servers='localhost:29092')

for _ in range(10):
    msg = json.dumps({'entity': 'MIT',
                      'category': 'Machine Learning',
                      'docID': uuid.uuid4().hex}).encode('utf-8')
    ack = producer.send('ner-finished', msg)
    metadata = ack.get()
