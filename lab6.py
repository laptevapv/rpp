from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Настройки подключения к БД
DB_CONFIG = {
    "host": "localhost",
    "database": "lab6",
    "user": "postgres",  
    "password": "",      
}

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

@app.route('/load', methods=['POST'])
def load_currency():
    data = request.json
    currency_name = data['currency_name']
    rate = data['rate']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование валюты
        cur.execute("SELECT * FROM currencies WHERE currency_name = %s", (currency_name,))
        if cur.fetchone():
            return jsonify({"error": "Currency already exists"}), 400
        
        # Добавляем новую валюту
        cur.execute(
            "INSERT INTO currencies (currency_name, rate) VALUES (%s, %s)",
            (currency_name, rate)
        )
        conn.commit()
        return jsonify({"message": "Currency added successfully"}), 200
    
    finally:
        cur.close()
        conn.close()

@app.route('/update_currency', methods=['POST'])
def update_currency():
    data = request.json
    currency_name = data['currency_name']
    new_rate = data['new_rate']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование валюты
        cur.execute("SELECT * FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Currency not found"}), 404
        
        # Обновляем курс
        cur.execute(
            "UPDATE currencies SET rate = %s WHERE currency_name = %s",
            (new_rate, currency_name)
        )
        conn.commit()
        return jsonify({"message": "Currency updated successfully"}), 200
    
    finally:
        cur.close()
        conn.close()

@app.route('/delete', methods=['POST'])
def delete_currency():
    data = request.json
    currency_name = data['currency_name']
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Проверяем существование валюты
        cur.execute("SELECT * FROM currencies WHERE currency_name = %s", (currency_name,))
        if not cur.fetchone():
            return jsonify({"error": "Currency not found"}), 404
        
        # Удаляем валюту
        cur.execute("DELETE FROM currencies WHERE currency_name = %s", (currency_name,))
        conn.commit()
        return jsonify({"message": "Currency deleted successfully"}), 200
    
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)