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

EX = Namespace("http://example.org/kst/")
def run_iita(matrix):
    df = pd.DataFrame(matrix)
    response = iita(df, v=1)
    return response["implications"]  # usually list of tuples (a,b)

def save_implications_ontology(implications, domain_id="latest_iita", out_dir="exports"):
    os.makedirs(out_dir, exist_ok=True)

    g = Graph()
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)

    domain_uri = EX[f"knowledgeDomain/{domain_id}"]
    g.add((domain_uri, RDF.type, EX.KnowledgeDomain))
    g.add((domain_uri, RDFS.label, Literal(domain_id)))
    g.add((domain_uri, EX.generatedAt, Literal(datetime.utcnow().isoformat(), datatype=XSD.dateTime)))

    items = {i for edge in implications for i in edge}
    for i in sorted(items):
        item_uri = EX[f"item/{i}"]
        g.add((item_uri, RDF.type, EX.Item))
        g.add((item_uri, RDFS.label, Literal(f"Item {i}")))

    for a, b in implications:
        g.add((EX[f"item/{a}"], EX.implies, EX[f"item/{b}"]))

    path = os.path.join(out_dir, f"{domain_id}.ttl")
    g.serialize(destination=path, format="turtle")
    return path

def build_ttl_from_edges(edges, nodes, domain_name):
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)

    domain_uri = EX[f"knowledgeDomain/{domain_name}"]
    g.add((domain_uri, RDF.type, EX.KnowledgeDomain))
    g.add((domain_uri, RDFS.label, Literal(domain_name)))
    g.add((domain_uri, EX.generatedAt, Literal(datetime.utcnow().isoformat(), datatype=XSD.dateTime)))

    def node_uri(idx):
        return EX[f"node/{nodes[idx]['id']}"]

    for i, n in enumerate(nodes):
        u = node_uri(i)
        g.add((u, RDF.type, EX.Item))
        g.add((u, RDFS.label, Literal(n.get("name", f"Item {i}"))))
        g.add((u, EX.inDomain, domain_uri))

    for a, b in edges:
        g.add((node_uri(a), EX.implies, node_uri(b)))

    return g.serialize(format="turtle")

@app.route("/iita", methods=["POST"])
def iitaEndpoint():
    matrix = request.get_json()
    print(matrix)

    implications = run_iita(matrix)
    print(implications)

    try:
        save_implications_ontology(implications, domain_id="latest_iita")
    except Exception as e:
        print("Ontology export failed:", str(e))

    return implications

@app.route("/iita/ontology", methods=["POST"])
def iitaOntologyEndpoint():
    payload = request.get_json()
    matrix = payload["matrix"]
    nodes = payload["nodes"]
    domain_name = payload.get("domainName", "latest_iita")

    if not matrix or len(matrix[0]) != len(nodes):
        return jsonify({
            "error": "nodes length must match matrix column count",
            "matrix_cols": len(matrix[0]) if matrix else 0,
            "nodes_len": len(nodes)
        }), 400

    implications = run_iita(matrix)
    edges = [list(x) for x in implications]  # make JSON-like pairs

    ttl = build_ttl_from_edges(edges, nodes, domain_name)
    return ttl, 200, {"Content-Type": "text/turtle"}

if __name__ == '__main__':
    app.run(debug=True)