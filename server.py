# server.py
"""
SAMRAKSHANA v2 - Cloud-ready Flask API
Endpoints:
 - POST /register      {device_id, token}  -> register device (local DB + optionally verify on-chain)
 - POST /data          {device_id, token, temperature, humidity} -> ingest sensor reading
 - GET  /devices       -> list registered devices
 - GET  /alerts        -> list recent alerts
 - GET  /latest/<id>   -> latest readings for a device
 - GET  /                 -> health check

CONFIG via ENV:
 - DATABASE_URL (default sqlite:////home/site/wwwroot/data/samrakshana.db)
 - PORT (default 5000)
 - DEBUG (0/1)
 - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, ADMIN_PHONE (for SMS)
 - BLOCKCHAIN_RPC (optional) - HTTP RPC to check smart contract
 - CONTRACT_ADDRESS (optional)
 - CONTRACT_ABI_PATH (optional)
"""
import os, hashlib, time, json
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, Integer, String, Float, BigInteger, Text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError
from collections import deque, defaultdict

# persistent path (works on Azure App Service and local)
DATA_DIR = os.environ.get("DATA_DIR", "/home/site/wwwroot/data")
os.makedirs(DATA_DIR, exist_ok=True)

DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DATA_DIR}/samrakshana.db")
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("DEBUG", "0").lower() in ("1", "true", "yes")

# Twilio envs are optional
TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.environ.get("TWILIO_FROM")
ADMIN_PHONE = os.environ.get("ADMIN_PHONE")

# blockchain config (optional, Phase 2)
BLOCKCHAIN_RPC = os.environ.get("BLOCKCHAIN_RPC")
CONTRACT_ADDRESS = os.environ.get("CONTRACT_ADDRESS")
CONTRACT_ABI_PATH = os.environ.get("CONTRACT_ABI_PATH")

# rate limiter
RATE_LIMIT_WINDOW = int(os.environ.get("RATE_LIMIT_WINDOW", "60"))
RATE_LIMIT_MAX = int(os.environ.get("RATE_LIMIT_MAX", "30"))

app = Flask(__name__)
CORS(app)

# SQLAlchemy
Base = declarative_base()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine)

class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    token_hash = Column(String, index=True)
    registered_at = Column(BigInteger)

class SensorData(Base):
    __tablename__ = "sensor_data"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    temperature = Column(Float)
    humidity = Column(Float)
    ts = Column(BigInteger)

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    device_id = Column(String, index=True)
    alert_type = Column(String)
    description = Column(Text)
    ts = Column(BigInteger)

def init_db():
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
    except OperationalError as e:
        app.logger.error("DB init failed: %s", e)

init_db()

# utilities
def now_ts(): return int(datetime.utcnow().timestamp())
def compute_token_hash(device_id: str, token: str) -> str:
    return hashlib.sha256(f"{device_id}:{token}".encode()).hexdigest()

# in-memory rate limiter (demo)
rate_buckets = defaultdict(lambda: deque())
def allowed_rate(device_id: str) -> bool:
    now = time.time()
    dq = rate_buckets[device_id]
    while dq and dq[0] < now - RATE_LIMIT_WINDOW:
        dq.popleft()
    if len(dq) >= RATE_LIMIT_MAX:
        return False
    dq.append(now)
    return True

# Twilio helper (optional)
def send_sms_via_twilio(body: str) -> bool:
    if not (TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_FROM and ADMIN_PHONE):
        app.logger.info("Twilio credentials not configured — skipping SMS.")
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        msg = client.messages.create(body=body, from_=TWILIO_FROM, to=ADMIN_PHONE)
        app.logger.info("Sent SMS sid=%s", getattr(msg, "sid", None))
        return True
    except Exception as e:
        app.logger.exception("Twilio send failed: %s", e)
        return False

# (Optional) blockchain verify helper placeholder
def verify_on_chain(device_id: str, token_hash: str) -> bool:
    # Phase 2: connect via web3.py to check registry contract (if configured)
    if not (BLOCKCHAIN_RPC and CONTRACT_ADDRESS and CONTRACT_ABI_PATH):
        return True  # treat as OK if blockchain is not set up (so dev can proceed)
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_RPC))
        with open(CONTRACT_ABI_PATH, "r") as f:
            abi = json.load(f)
        contract = w3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)
        return contract.functions.verify(device_id, token_hash).call()
    except Exception as e:
        app.logger.exception("Blockchain verify error: %s", e)
        return False

# Endpoints
@app.route("/", methods=["GET"])
def health():
    return jsonify({"ok": True, "timestamp": now_ts(), "db": DATABASE_URL}), 200

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    device_id = data.get("device_id")
    token = data.get("token")
    if not device_id or not token:
        return jsonify({"error": "device_id and token required"}), 400
    token_hash = compute_token_hash(device_id, token)
    # optional on-chain verify
    if not verify_on_chain(device_id, token_hash):
        return jsonify({"error": "device not registered on-chain"}), 403
    session = SessionLocal()
    d = Device(device_id=device_id, token_hash=token_hash, registered_at=now_ts())
    session.add(d)
    session.commit()
    session.close()
    return jsonify({"registered": True, "device_id": device_id}), 201

@app.route("/data", methods=["POST"])
def ingest_data():
    j = request.get_json(silent=True) or {}
    device_id = j.get("device_id")
    token = j.get("token")
    try:
        temperature = float(j.get("temperature"))
        humidity = float(j.get("humidity"))
    except Exception:
        return jsonify({"error": "temperature and humidity numeric required"}), 400
    if not device_id or not token:
        return jsonify({"error": "auth required"}), 401
    if not allowed_rate(device_id):
        session = SessionLocal()
        a = Alert(device_id=device_id, alert_type="rate_limit", description="rate limit exceeded", ts=now_ts())
        session.add(a); session.commit(); session.close()
        return jsonify({"error": "rate limit exceeded"}), 429
    token_hash = compute_token_hash(device_id, token)
    session = SessionLocal()
    found = session.query(Device).filter(Device.device_id == device_id, Device.token_hash == token_hash).first()
    if not found:
        a = Alert(device_id=device_id, alert_type="auth_fail", description="invalid token or unregistered device", ts=now_ts())
        session.add(a); session.commit(); session.close()
        return jsonify({"error": "unauthorized"}), 403
    sd = SensorData(device_id=device_id, temperature=temperature, humidity=humidity, ts=now_ts())
    session.add(sd)
    session.commit()
    # anomaly detection (simple)
    window = int(os.environ.get("ANOMALY_WINDOW", "10"))
    tolerance = float(os.environ.get("ANOMALY_TOLERANCE", "8.0"))
    recent = session.query(SensorData).filter(SensorData.device_id == device_id).order_by(SensorData.ts.desc()).limit(window).all()
    is_anom = False; desc = ""
    if recent and len(recent) >= 3:
        temps = [r.temperature for r in recent]
        avg_t = sum(temps)/len(temps)
        if abs(temperature - avg_t) > tolerance:
            is_anom = True
            desc = f"temp deviation {temperature} vs avg {avg_t:.2f}"
    if is_anom:
        a = Alert(device_id=device_id, alert_type="anomaly", description=desc, ts=now_ts())
        session.add(a); session.commit()
        # send SMS (best-effort)
        try:
            send_sms_via_twilio(f"Anomaly detected on {device_id}: {desc}")
        except Exception:
            app.logger.exception("SMS send failed")
    session.close()
    return jsonify({"ok": True, "anomaly": is_anom, "desc": desc}), 200

@app.route("/devices", methods=["GET"])
def list_devices():
    session = SessionLocal()
    rows = session.query(Device).order_by(Device.registered_at.desc()).all()
    out = [{"device_id": r.device_id, "registered_at": r.registered_at} for r in rows]
    session.close()
    return jsonify(out), 200

@app.route("/alerts", methods=["GET"])
def list_alerts():
    session = SessionLocal()
    rows = session.query(Alert).order_by(Alert.ts.desc()).limit(200).all()
    out = [{"device_id": r.device_id, "type": r.alert_type, "desc": r.description, "ts": r.ts} for r in rows]
    session.close()
    return jsonify(out), 200

@app.route("/latest/<device_id>", methods=["GET"])
def latest(device_id):
    session = SessionLocal()
    rows = session.query(SensorData).filter(SensorData.device_id == device_id).order_by(SensorData.ts.desc()).limit(100).all()
    out = [{"temperature": r.temperature, "humidity": r.humidity, "ts": r.ts} for r in rows]
    session.close()
    return jsonify(out), 200

if __name__ == "__main__":
    # Local dev: python server.py
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
