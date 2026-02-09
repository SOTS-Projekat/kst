from flask import Flask, request, jsonify
import pandas as pd
from learning_spaces.kst import iita
from flask_cors import CORS

from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF, RDFS, XSD
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

def save_implications_ontology(implications, domain_id="domain1", out_dir="exports"):   #pozovi iita, napravi realan domen ko ranije i od output napravi ontologogiju uz pomoc rdf.
    os.makedirs(out_dir, exist_ok=True)

    g = Graph()
    EX = Namespace("http://example.org/kst/")
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)

    # Basic schema-ish bits (lightweight)
    g.add((EX.Item, RDF.type, RDFS.Class))
    g.add((EX.KnowledgeDomain, RDF.type, RDFS.Class))
    g.add((EX.implies, RDF.type, RDF.Property))

    domain = EX[f"knowledgeDomain/{domain_id}"]
    g.add((domain, RDF.type, EX.KnowledgeDomain))
    g.add((domain, RDFS.label, Literal(domain_id)))
    g.add((domain, EX.generatedAt, Literal(datetime.utcnow().isoformat(), datatype=XSD.dateTime)))

    items = set()
    for a, b in implications:
        items.add(a)
        items.add(b)

    for i in sorted(items):
        item_uri = EX[f"item/{i}"]
        g.add((item_uri, RDF.type, EX.Item))
        g.add((item_uri, RDFS.label, Literal(f"Item {i}")))

    for a, b in implications:
        g.add((EX[f"item/{a}"], EX.implies, EX[f"item/{b}"]))

    path = os.path.join(out_dir, f"{domain_id}.ttl")
    g.serialize(destination=path, format="turtle")
    return path


@app.route("/iita", methods=["POST"])
def iitaEndpoint():
    request_data = request.get_json()
    results = request_data

    print(request_data)
    data_frame = pd.DataFrame(results)
    response = iita(data_frame, v=1)
    print(response['implications'])

    try:
        save_implications_ontology(response['implications'], domain_id="latest_iita")
    except Exception as e:
        print("Ontology export failed:", str(e))

    return response['implications']


if __name__ == '__main__':
    app.run(debug=True)