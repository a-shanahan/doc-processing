# Layout Parser
Unstructured text is processed using the Layout Parser model which is hosted as a Flask app. 

## Setup
Container is internally exposed on port 5060. This will need to be mapped to a port of the local machine. 
For local testing, to build and run container:

```shell
cd Layout-Parser
docker build . -t layout-p:latest
docker run -d -p 5060:5060 layout-p:latest
```

The container is running detached mode (-d). It is possible to attach to the container from with another 
terminal window by using the command:
```shell
docker ps
# Select name of container
docker attach <container name>
```

The container expects a PDF file to be posted which you sent through and through a Tesseract OCR engine. The results are 
loaded into ElasticSearch using the bulk upload functionality.

No messages are passed to Kafka as the PySpark job runs on a schedule and will be used to process documents on bulk. 
If a notification is required back to the user to indicate the processing has been completed then this should be added 
here.