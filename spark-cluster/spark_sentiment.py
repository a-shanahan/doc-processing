"""
This script contains PySaprk streaming code for detecting the sentiment of unstructured text. It monitors
the 'sentiment-ready' Kafka topic and uses the TextBlob library to detect polarity and subjectivity.
Results are published to the 'sentiment-finished' Kafka topic. This code has been developed on a standalone
cluster so the streaming app is periodically terminated to allow other scripts to be executed.
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
import json
from pyspark.sql import functions as F
from textblob import TextBlob

appName = "Sentiment"
CHECKPOINT_LOCATION = "/tmp"


@udf
def preprocessing(lines):
    words = lines.select(explode(split(lines.value, "t_end")).alias("word"))
    words = words.na.replace('', None)
    words = words.na.drop()
    words = words.withColumn('word', F.regexp_replace('word', r'http\S+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '@\w+', ''))
    words = words.withColumn('word', F.regexp_replace('word', '#', ''))
    words = words.withColumn('word', F.regexp_replace('word', 'RT', ''))
    words = words.withColumn('word', F.regexp_replace('word', ':', ''))
    return words


# text classification
def polarity_detection(text):
    return TextBlob(text).sentiment.polarity


def subjectivity_detection(text):
    return TextBlob(text).sentiment.subjectivity


@udf
def text_classification(words):
    # polarity detection
    polarity = polarity_detection(words)
    # subjectivity detection
    subjectivity = subjectivity_detection(words)
    return json.dumps({'polarity': polarity,
                       'subjectivity': subjectivity})


spark = SparkSession.builder. \
    appName(appName) \
    .config('spark.jars.packages',
            ['org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0']) \
    .config('spark.streaming.stopGracefullyOnShutdown', 'true') \
    .config("spark.driver.memory", "8G") \
    .config("spark.driver.maxResultSize", "0") \
    .config("spark.kryoserializer.buffer.max", "2000M") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")
kafka_servers = "kafka:9092"
text_classification_udf = spark.udf.register("text_classification", text_classification)

df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_servers) \
    .option("subscribe", "sentiment-ready") \
    .load()

sample_schema = (
    StructType()
    .add("id", StringType())
    .add("content", StringType())
)

df = df.select(
    from_json(col("value").cast("string"), sample_schema).alias("value"),
).select("value.id", "value.content")


df.withColumn(
    "value",
    text_classification(col("content"))) \
    .select(col('id').alias("key"), "value") \
    .writeStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafka_servers) \
    .option("checkpointLocation", CHECKPOINT_LOCATION) \
    .option("topic", "sentiment-finished") \
    .start() \
    .awaitTermination(timeout=240)
