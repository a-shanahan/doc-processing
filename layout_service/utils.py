"""
This script contains a number of helper functions used by the main app.py file.
"""
import uuid
import re
import os
from typing import Tuple
import layoutparser as lp
import cv2
from pdf2image import convert_from_path
import numpy as np
from elasticsearch7 import Elasticsearch, NotFoundError
from elasticsearch7.helpers import bulk


def attempt_es(index_name: str):
    """
    Connect to ElasticSearch instance
    :return: ElasticSearch connection
    """
    try:
        es = elastic_connect(index_name)
        return es
    except ConnectionError:
        return None


def initialise_model(conf_thresh: float = 0.5):
    """
    Download model on application initialisation. Accepts a confidence threshold as input.

    :param conf_thresh: Model confidence threshold
    :return: model: Detectron2 model
    """
    # Download model
    model = lp.Detectron2LayoutModel(config_path='lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config',
                                     extra_config=['MODEL.ROI_HEADS.SCORE_THRESH_TEST', conf_thresh],
                                     label_map={0: 'Text', 1: 'Title', 2: 'List', 3: 'Table', 4: 'Figure'})
    return model


def parse_layout(doc_id: str, es, es_index, model, filename: str, upload_folder: str) -> Tuple:
    """
    Reads file from directory and converts each page to a numpy array and stored within a list.

    :param es_index: ElasticSearch index name
    :param doc_id: Document UID
    :param es: ElasticSearch connection
    :param upload_folder: Location of file system which stores uploade data
    :param model: Detectron2 model
    :param filename: Secure name of file
    :return: record count, ids: Number of upload results and their ElasticSearch UIDs.
    """
    file_path = os.path.join(upload_folder, filename)
    if re.search("pdf$", file_path):
        # Convert pdf 2 images
        # One image per page
        pdf_2_image = convert_from_path(file_path)
        # Convert to numpy array
        dta = [np.asarray(i) for i in pdf_2_image]
    elif re.search("png$|jpeg$", file_path):
        dta = cv2.imread(file_path)
    else:
        # This should have been caught on upload
        raise TypeError('Incorrect file type')
    # Initialise OCR
    ocr_engine = lp.TesseractAgent()
    # Iterate over pages
    ids = []
    for page in dta:
        layout = model.detect(page)
        # Send detected segments to OCR
        page_results = []
        for block in layout:
            segment = block.pad(left=20, right=20, bottom=15).crop_image(page)
            text = ocr_engine.detect(segment)
            _id = uuid.uuid4().hex
            ids.append(_id)
            resp = {
                "_index": es_index,
                "_id": _id,
                "_source": {
                    'Doc_id': doc_id,
                    'Co-ordinates': {'x1': block.coordinates[0],
                                     'y1': block.coordinates[1],
                                     'x2': block.coordinates[2],
                                     'y2': block.coordinates[3]},
                    'Text': text,
                    'Type': block.type,
                    'Score': block.score,
                    'Processed': 'false'}
            }
            page_results.append(resp)
        # Bulk upload to ElasticSearch
        bulk(es, page_results)
    es.indices.refresh(index=es_index)
    record_count = es.cat.count(index=es_index, format="json")
    return record_count, ids


def elastic_connect(index_name: str):
    """
    Initialise connection to ElasticSearch and create index

    :param index_name: ElasticSearch index name
    :return: ElasticSearch connection
    """
    es = Elasticsearch(["http://doc_elasticsearch:9200"], request_timeout=30)

    mappings = {
        "properties": {
            "UID": {"type": "text"},
            "Co-ordinates": {"type": "nested"},
            "Text": {"type": "text", "analyzer": "standard"},
            "Type": {"type": "text", "analyzer": "standard"},
            "Score": {"type": "float"},
            "Processed": {"type": "boolean"}
        }
    }
    try:
        es.indices.delete(index=index_name)
    except NotFoundError:
        es.indices.create(index=index_name, mappings=mappings)
    return es
