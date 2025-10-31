from flask import Flask, request, jsonify
import psycopg2

app = Flask(__name__)

# Database connection details
DB_HOST = "samrakshana-db.postgres.database.azure.com"
DB_NAME = "iot_data_db"
DB_USER = "admsunnyin"
DB_PASS = "YourPasswordHere"  # replace with your real password

@app.route('/insert', methods=['POST'])
def insert_data():
    try:
        data = request.json
        device_id = data['device_id']
        temperature = data['temperature']
        humidity = data['humidity']

        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host="samrakshana-db.postgres.database.azure.com",
            database="iot_data_db",
            user="admsunnyin",
            password="Nadeem@2025#",
            sslmode='require'
        )
        cur = conn.cursor()

        # Insert into the table
        cur.execute("""
            INSERT INTO device_data (device_id, temperature, humidity)
            VALUES (%s, %s, %s)
        """, (device_id, temperature, humidity))
        
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"status": "success", "message": "Data inserted successfully"}), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/fetch', methods=['GET'])
def fetch_data():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM device_data ORDER BY timestamp DESC LIMIT 10;")
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"status": "success", "data": rows})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
