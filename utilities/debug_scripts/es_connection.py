"""
Test connection to ElasticSearch instance
"""
from elasticsearch7 import Elasticsearch

es = Elasticsearch(["http://localhost:9200"], request_timeout=30)

myquery = '{ "query": { "match_all": {} }}'

res = es.search(index="test-index", body=myquery)
print(res)

for doc in res['hits']['hits']:
    print("%s) %s" % (doc['_id'], doc['_source']['content']))
