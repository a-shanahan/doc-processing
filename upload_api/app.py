"""
This scipt is the upload api that users send documents to via http. The document is subjected to simple
tests before being stored in a different directory.
"""
import json
import os
import logging
import uuid
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from kafka import KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Flask config
app = Flask(__name__)
app.secret_key = uuid.uuid4().hex
app.config['Upload'] = '/file_storage'


def allowed_file(filename: str) -> bool:
    """
    Check if file extension is in allowed list

    :param filename:
    :return: Bool
    """
    # Allowable file extensions
    allowed_extensions = ['pdf', 'jpeg', 'png']
    if '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions:
        return True
    else:
        return False


@app.route('/')
def hello_world():
    logger.info('Hello logs')
    return 'Hello world'


@app.route('/upload', methods=["POST"])
def upload():
    producer = KafkaProducer(bootstrap_servers='kafka:9092', api_version=(0, 10, 1))
    # Create document ID
    doc_id = uuid.uuid4().hex
    if 'file' not in request.files:
        resp = jsonify({'Error': 'No file present'})
        resp.status_code = 400
        return resp
    file = request.files['file']
    if allowed_file(file.filename):
        # Clean filename to ensure only suffix and no spaces
        filename = secure_filename(file.filename)
        # Save file to file storage area
        file.save(os.path.join(app.config['Upload'], filename))
        # Create kafka message
        msg = json.dumps({'filename': filename,
                          'docId': doc_id}).encode('utf-8')
        # Send notification to Kafka
        ack = producer.send('new-document', msg)
        ack.get()
        resp = jsonify({'Document Uploaded': doc_id})
        resp.status_code = 201
        return resp
    else:
        resp = jsonify({'Error': 'Incorrect file type'})
        resp.status_code = 400
        return resp
