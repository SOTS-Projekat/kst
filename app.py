import os
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, OWL, XSD

from learning_spaces.kst import iita

app = Flask(__name__)
CORS(app)

EX = Namespace("http://example.org/eks/schema#")
SCHEMA_PATH = "file:///C:/Users/Administrator/Documents/GitHub/Owl_Ontologija_NEW/schema.owl"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(BASE_DIR, "exports")

def save_rdf(content: str, domain_name: str, extension: str) -> str:
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    safe = domain_name.replace(" ", "_")
    path = os.path.join(EXPORT_DIR, f"{safe}.{extension}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def build_graph_from_edges(edges, nodes, domain_name):
    g = Graph()
    g.bind("ex", EX)
    g.bind("rdfs", RDFS)
    g.bind("owl", OWL)

    safe_domain = domain_name.replace(" ", "_")   # Replace spaces with underscores for clean URIs
    domain_uri = EX[f"domain/{safe_domain}"]

    # Create the ontology and import the schema
    ontology_uri = EX[f"ontology/{safe_domain}"]
    g.add((ontology_uri, RDF.type, OWL.Ontology))
    g.add((ontology_uri, OWL.imports, URIRef(SCHEMA_PATH)))

    # Create the Domain instance (using schema vocabulary)
    g.add((domain_uri, RDF.type, EX.Domain))
    g.add((domain_uri, EX.name, Literal(domain_name)))
    g.add((domain_uri, RDFS.label, Literal(domain_name)))  # For Protégé display
    g.add((domain_uri, EX.generatedAt, Literal(datetime.now(timezone.utc).isoformat(), datatype=XSD.dateTime)))

    def competency_uri(idx: int):
        return EX[f"competency/{nodes[idx]['id']}"]

    # Create Competency instances
    for i, n in enumerate(nodes):
        u = competency_uri(i)
        comp_name = n.get("name", f"Competency {i}")
        g.add((u, RDF.type, EX.Competency))
        g.add((u, EX.name, Literal(comp_name)))
        g.add((u, RDFS.label, Literal(comp_name)))  # For Protégé display

        # Domain hasCompetency Competency (reversed from inDomain)
        g.add((domain_uri, EX.hasCompetency, u))

    # Create prerequisite relationships (using schema's prerequisiteOf)
    for a, b in edges:
        g.add((competency_uri(a), EX.prerequisiteOf, competency_uri(b)))

    return g


@app.route("/iita", methods=["POST"])
def iitaEndpoint():
    request_data = request.get_json()
    results = request_data

    #print(request_data)
    data_frame = pd.DataFrame(results)
    response = iita(data_frame, v=1)
    #print(response["implications"])

    return response["implications"]


@app.route("/iita/rich", methods=["POST"])
def iitaRichEndpoint():
    payload = request.get_json()

    matrix = payload["matrix"]
    items = payload["items"]
    domain = payload.get("domain", {})
    domain_name = domain.get("name", "latest_iita")

    nodes = [{"id": it["nodeId"], "name": it.get("label", f"Item {it.get('col', '?')}")} for it in items]

    if not matrix or len(matrix[0]) != len(nodes):
        return jsonify({
            "error": "items/nodes length must match matrix column count",
            "matrix_cols": len(matrix[0]) if matrix else 0,
            "nodes_len": len(nodes)
        }), 400

    df = pd.DataFrame(matrix)
    response = iita(df, v=1)
    edges = [list(x) for x in response["implications"]]

    g = build_graph_from_edges(edges, nodes, domain_name)

    # Serialize to OWL/XML format
    owl_content = g.serialize(format="xml")

    # Save OWL file
    owl_path = save_rdf(owl_content, domain_name, "owl")

    return jsonify({
        "status": "ok",
        "savedTo": owl_path
    })


if __name__ == "__main__":
    app.run(debug=True)
