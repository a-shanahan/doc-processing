"""
This script contains helper functions to text connections to ElasticSearch, format data and
send messages to Kafka.
"""
import json
from typing import Dict
from elasticsearch7 import Elasticsearch, NotFoundError
from kafka.errors import NoBrokersAvailable


def attempt_es(index_name):
    """
    Connect to ElasticSearch instance
    :return: ElasticSearch connection
    """
    try:
        es = elastic_connect(index_name)
        return es
    except ConnectionError:
        return None


def send_to_kafka(article, id_, producer) -> None:
    """
    Send the extracted content to the 'sentiment'ready' Kafka topic.

    :param article: BS4 container
    :param id_: UID of article
    :param producer: Kafka Producer
    """
    try:
        key = list(article.keys())[0]
        msg = json.dumps({'id': id_,
                          'content': article.get(key)['body']}).encode('utf-8')
        ack = producer.send('sentiment-ready', msg)
        _ = ack.get()
    except (AttributeError, NoBrokersAvailable) as e:
        pass


def es_format(article, article_id, es_index) -> Dict:
    """
    Format the article content into the ElasticSearch schema.
    :param article: BS4 container
    :param article_id: Article UID
    :param es_index: Elastic search index name
    :return: ElasticSearch formatted dictionary
    """
    key = list(article.keys())[0]
    resp = {
        "_index": es_index,
        "_id": article_id,
        "_source": {
            'Link': key,
            'Title': article.get(key)['title'],
            'Text': article.get(key)['body'],
            'Processed': 'false'}
    }
    return resp


def elastic_connect(index_name: str):
    """
    Initialise connection to ElasticSearch and create index
    :return: ElasticSearch connection
    """
    es = Elasticsearch(["http://localhost:9200"], request_timeout=30)

    mappings = {
        "properties": {
            "Link": {"type": "text"},
            "Title": {"type": "text", "analyzer": "standard"},
            "Text": {"type": "text", "analyzer": "standard"},
            "Processed": {"type": "boolean"}
        }
    }
    try:
        es.indices.delete(index=index_name)
    except NotFoundError:
        es.indices.create(index=index_name, mappings=mappings)
    return es
