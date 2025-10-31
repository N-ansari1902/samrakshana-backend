import requests
import random
import time

SERVER_URL = "http://127.0.0.1:5000/insert"
DEVICE_ID = "esp32_simulated_01"

while True:
    # Generate random but realistic temperature/humidity
    temperature = round(random.uniform(20.0, 35.0), 2)
    humidity = round(random.uniform(40.0, 90.0), 2)
    
    payload = {
        "device_id": DEVICE_ID,
        "temperature": temperature,
        "humidity": humidity
    }
    
    try:
        response = requests.post(SERVER_URL, json=payload)
        print(f"[{time.strftime('%H:%M:%S')}] Sent: {payload} | Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending data: {e}")
    
    time.sleep(10)  # wait 10 seconds between sends
