# NLP with Spark
PySpark is used to perform named entity recognition on the extracted text. This is done using spaCy but can be 
changed if needed. 

A Spark cluster is created with a single master and worker node. They both use the same dockerfile to build the container 
but the master node has additional commands that are run on start-up to schedule a spark-submit job using cron.

Data is read from ElasticSearch where the 'processed' boolean flag is set to False. The NER processing is contained within a 
UDF (user defined function) that is applied to the raw text. Named entities are formed as:
```json lines
{
  "ner": [
    {
      "entity": 'Github',
      "category": 'Organisation'
    }
  ]
}
```

The data is loaded into ElasticSearch and the 'processed' boolean flag updated to True.

The individual records are also passed to Kafka as messages to allow for further processing. 
The spark installation file is not provided, however it can be downloaded using:

```shell
PARK_VERSION=3.3.0
HADOOP_VERSION=3
wget --no-verbose -O apache-spark.tgz "https://archive.apache.org/dist/spark/spark-${SPARK_VERSION}/spark-${SPARK_VERSION}-bin-hadoop${HADOOP_VERSION}.tgz" \
```