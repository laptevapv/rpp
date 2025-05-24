from flask import Flask, request, jsonify

app = Flask(__name__)

# Статические курсы валют
STATIC_RATES = {
    "USD": 92.45,
    "EUR": 99.87
}

@app.route("/rate", methods=["GET"])
def get_rate():
    try:
        currency = request.args.get("currency", "").upper()

        if currency not in STATIC_RATES:
            return jsonify({"message": "UNKNOWN CURRENCY"}), 400

        return jsonify({"rate": STATIC_RATES[currency]}), 200

    except Exception as e:
        print("Ошибка сервера:", e)
        return jsonify({"message": "UNEXPECTED ERROR"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
