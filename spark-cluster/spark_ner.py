"""
This script contains PySpark code for detecting Named Entities from unstructured text.
The script reads data from ElasticSearch using a boolean query and updates the flag after
processing. It also publishes the IDs to the 'ner-finished' Kafka topic.
"""
from pyspark.sql import SparkSession, SQLContext
from pyspark.sql.functions import *
import spacy
import json
import re

NLP = None
kafka_servers = "kafka:9092"


def get_spacy_magic_for(lang="en_core_web_sm"):
    global NLP
    if NLP is None:
        NLP = {}
    if lang not in NLP:
        NLP[lang] = spacy.load(lang)
    return NLP[lang]


def spacy_tokenize(row):
    """
    Extracts named entities and the corresponding label from text
    :param row: String
    :return: List of dictionaries
    """
    # Note this is expensive, in practice you would use something like SpacyMagic, see footnote for link; which caches
    # spacy.load so it isn’t happening multiple times
    nlp = get_spacy_magic_for()
    doc = nlp(row)
    result = [
        {"entity": re.sub('\n', ',', entity.text), "category": entity.label_}
        for entity in doc.ents]
    return json.dumps(result)


@udf
def pandas_tokenize(text):
    return spacy_tokenize(text)


# To prevent re-using same spark context if anything changes
try:
    spark.sparkContext.stop()
except NameError:
    pass

spark = SparkSession.builder \
    .appName("NER Processing") \
    .config("es.nodes", "http://doc_elasticsearch") \
    .config("es.port", "9200") \
    .config("es.read.field.as.array.include", "hits") \
    .getOrCreate()
# This is needed for local testing
# .config("es.nodes.wan.only", "true") \
# .config("es.nodes.discovery", "false") \

tokenize_pandas = spark.udf.register("tokenize_pandas", pandas_tokenize)

ner_context = SQLContext(spark)

# Query for records that are yet to be processed
myquery = '{ "query": { ' \
          ' "match": {' \
          '     "Processed": "false"} ' \
          '}}'

es_reader = ner_context.read.format("org.elasticsearch.spark.sql") \
    .option("es.nodes", "http://doc_elasticsearch") \
    .option("es.port", "9200") \
    .option("es.query", myquery) \
    .option("es.read.metadata", True)

es_frame = es_reader.load("document-index")

try:
    es_results = es_frame.select("Doc_id", "_metadata._id", "Text")

    v = es_results.select(col("Doc_id").cast("string").alias('key'),
                          pandas_tokenize(es_results.Text).alias('value')). \
        select('key', explode(split(col("value"), "\{")).alias("word-2"))

    x = v.where(col("word-2").contains('entity')).withColumn('word-2', regexp_replace('word-2', "\}|\]|,\s*$", ""))
    o = x.withColumn('value', concat(lit('{"docID": "'), col('key'), lit('", '), col('word-2'), lit('}'))). \
        select('value')

    # Write Spark Data frame to Kafka topic.
    o.select('value') \
        .write \
        .format("kafka") \
        .option("kafka.bootstrap.servers", kafka_servers) \
        .option("topic", 'ner-finished') \
        .save()

    # Update records in ElasticSearch to indicate they have been processed
    processed = es_results.select(expr("_id as id")).withColumn('Processed', lit(True))

    es_conf = {
        "es.mapping.id": "id",
        "es.mapping.exclude": "id",
        "es.write.operation": "update"
    }

    processed.write.format("org.elasticsearch.spark.sql") \
        .options(**es_conf) \
        .mode("append") \
        .save("document-index")

except AttributeError:
    print('No data to load')
    # No data to load
