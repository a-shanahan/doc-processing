#!/bin/bash
/opt/spark/bin/spark-submit --master spark://spark-master:7077 --packages org.elasticsearch:elasticsearch-spark-30_2.12:7.13.3,org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0 --driver-memory 1G --executor-memory 1G /spark_ner.py
