"""
This script scrapes the Top 10 News articles from the BBC News website and publishes the article text
to the 'sentiment-ready' Kafka topic. The function executes 10 times in a row with a 1 minutes wait between
loops. The results are uploaded to an ElasticSearch index called 'bbc-new'.
"""
import logging
import time
import uuid
from scrape import WebSite
from utils import *
from kafka import KafkaProducer
from elasticsearch7.helpers import bulk

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Kafka connection details.
producer = KafkaProducer(bootstrap_servers='localhost:29092', api_version=(0, 10, 1))


def main(link: str, es_index, es_connection) -> None:
    step = 1
    while True:
        logger.info(f'New loop {step}')
        content = WebSite(link).news
        es_results = []
        for article in content:
            article_id = uuid.uuid4().hex
            send_to_kafka(article, article_id, producer)
            es_results.append(es_format(article, article_id, es_index))
        # Bulk upload to ElasticSearch
        bulk(es_connection, es_results)
        es_connection.indices.refresh(index=es_index)
        time.sleep(60)
        step += 1
        if step > 10:
            break


if __name__ == '__main__':
    url = 'https://www.bbc.com/news'
    # ElasticSearch index name to store results
    index = 'bbc-news'
    es_connect = attempt_es(index)
    main(url, index, es_connect)
