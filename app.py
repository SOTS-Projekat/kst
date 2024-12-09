from flask import Flask, request, jsonify
import pandas as pd
from learning_spaces.kst import iita
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route("/iita", methods=["POST"])
def iitaEndpoint():
    request_data = request.get_json()
    # print(request_data)
    results = request_data
    # input = {}
    # for res in results:
    #     input[res["studentId"]] = res["responses"]

    print(request_data)
    data_frame = pd.DataFrame(results)
    response = iita(data_frame, v=1)
    print(response['implications'])
    # print(pd.Series(response).to_json(orient="values"))
    # return pd.Series(response).to_json(orient="values")
    return response['implications']

# Pokretanje Flask servera
if __name__ == '__main__':
    app.run(debug=True)
