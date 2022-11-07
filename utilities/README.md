# Utility scripts

This directory contains a number of scripts to help debug the application, setup Neo4j streaming and upload a file. 

## Upload a file
The application utilises Layout Parser to identify sections of text within a document and then perform OCR on the focussed 
elements. The [upload_file.py](upload_file.py) script provides an example of doing this with one document. 

First create a virtual environment, install the packages and then execute the script:

```shell
python3 -m venv venv
source venv/bin/activate
python3 upload_file.py
```

## Debug scripts
A collection of scripts are provided to test the functionality of ElasticSearch and to draw an image around the sections 
of text Layout Parser has identified. 