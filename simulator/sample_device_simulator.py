# sample_device_simulator.py
import requests, random, time, sys

# Set API endpoint: change to your Azure URL if needed
API_BASE = "http://localhost:5000"
DEVICE_ID = "simulator_01"
DEVICE_TOKEN = "secret123"

FORCE_ANOMALY_AFTER = int(sys.argv[1]) if len(sys.argv) > 1 else 0
count = 0

def register():
    try:
        r = requests.post(f"{API_BASE}/register", json={"device_id": DEVICE_ID, "token": DEVICE_TOKEN}, timeout=5)
        print("REGISTER:", r.status_code, r.text)
    except Exception as e:
        print("REGISTER ERROR:", e)
        sys.exit(1)

def send():
    global count
    while True:
        count += 1
        # normal range
        temp = round(random.uniform(25.0, 30.0), 2)
        hum = round(random.uniform(40.0, 55.0), 2)
        # force anomaly for demo (high temp)
        if FORCE_ANOMALY_AFTER and count >= FORCE_ANOMALY_AFTER:
            temp = round(random.uniform(60.0, 80.0), 2)

        payload = {"device_id": DEVICE_ID, "token": DEVICE_TOKEN, "temperature": temp, "humidity": hum}
        try:
            r = requests.post(f"{API_BASE}/data", json=payload, timeout=5)
            print("DATA:", r.status_code, r.text, "|", payload)
        except Exception as e:
            print("DATA ERROR:", e)
        time.sleep(3)

if __name__ == "__main__":
    print("Simulator starting, API_BASE =", API_BASE)
    register()
    send()
