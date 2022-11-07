# Upload API
Files can be uploaded to the application by sending a POST request containing the file to the /upload endpoint.

The endpoint is hosted as a Flask application which is exposed on port 5050.

An example script to upload a file can be found in [upload_file.py](../utilities/upload_file.py).

The api stores the uploaded file in a directory that has been mounted with the Layout Parser container. 
It performs some simple checks on the file name to ensure it matches the correct format. Allowed formats are:
- PDF
- JPEG
- PNG

Once the file has been checked and stored a message is sent to a Kafka Topic which the Layout Parser
is subscribed. The response includes the unique identifier used for the document. This can be used 
to search for the data in ElasticSearch.
