from flask import Flask, request, jsonify
import pandas as pd
from learning_spaces.kst import iita

app = Flask(__name__)

@app.route('/api/iita', methods=['POST'])
def run_iita():
    try:
        # Uzimanje JSON podataka iz POST zahteva
        data = request.get_json()

        # Pretvaranje podataka u DataFrame
        data_frame = pd.DataFrame(data['responses'])

        # Pozivanje IITA algoritma
        response = iita(data_frame, v=data.get('v', 1))

        # Slanje rezultata kao JSON
        return response['implications']
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# Pokretanje Flask servera
if __name__ == '__main__':
    app.run(debug=True)
