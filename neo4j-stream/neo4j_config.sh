#!/bin/bash
curl -X POST http://localhost:8083/connectors -H 'Content-Type:application/json' -H 'Accept:application/json' -d @contrib.sink.string-json.neo4j.json