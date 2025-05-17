from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Настройки подключения к PostgreSQL
DB_CONFIG = {
    "host": "localhost",
    "database": "lab6",
    "user": "postgres",  
    "password": "",      
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.route('/convert', methods=['GET'])
def convert_currency():
    currency_name = request.args.get('currency_name')
    amount = request.args.get('amount')
    
    if not currency_name or not amount:
        return jsonify({"error": "Missing required parameters"}), 400
    
    try:
        amount = float(amount)
    except ValueError:
        return jsonify({"error": "Amount must be a number"}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование валюты и получаем курс
        cur.execute("SELECT rate FROM currencies WHERE currency_name = %s", (currency_name,))
        result = cur.fetchone()
        
        if not result:
            return jsonify({"error": "Currency not found"}), 404
        
        rate = result['rate']
        converted_amount = amount * rate
        
        return jsonify({
            "original_amount": amount,
            "currency_name": currency_name,
            "rate": rate,
            "converted_amount": round(converted_amount, 2)
        }), 200
    
    finally:
        cur.close()
        conn.close()

@app.route('/currencies', methods=['GET'])
def get_all_currencies():
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("SELECT currency_name, rate FROM currencies ORDER BY currency_name")
        currencies = cur.fetchall()
        return jsonify(currencies), 200
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)