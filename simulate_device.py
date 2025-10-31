import time
import requests
import random

BASE_URL = "http://127.0.0.1:5000"
DEVICE_ID = "ESP32_DEV_01"
TOKEN = "mysecret"

def push_data():
    while True:
        temperature = round(random.uniform(25.0, 40.0), 2)
        humidity = round(random.uniform(30.0, 60.0), 2)

        res = requests.post(
            f"{BASE_URL}/data",
            json={
                "device_id": DEVICE_ID,
                "token": TOKEN,
                "temperature": temperature,
                "humidity": humidity
            },
        )

        print(f"Sent → Temp: {temperature}, Humidity: {humidity}, Status: {res.status_code}")
        time.sleep(5)

if __name__ == "__main__":
    push_data()
