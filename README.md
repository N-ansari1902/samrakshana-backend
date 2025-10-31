# SAMRAKSHANA v2 — IoT Observability (Cloud + Blockchain ready)

Quick start (local, no hardware required)

1. Create folder `samrakshana_v2` and paste all files.
2. Install Python 3.11+ and Docker (optional).
3. Local Python test:
   - Create virtual environment:
     python -m venv .venv
     .venv\Scripts\activate   (Windows) or source .venv/bin/activate (Linux/Mac)
   - pip install -r requirements.txt
   - python server.py
   - open http://localhost:5000/ (health)
4. Run dashboard:
   - cd dashboard
   - pip install -r requirements.txt
   - streamlit run dashboard.py
   - open http://localhost:8501
5. Run simulator:
   - python simulator/sample_device_simulator.py
   - Change API url in simulator if using Azure deployment.

Deploy to Azure:
 - Build image, push to ACR, and create Web App for Containers (use Dockerfile).
 - Ensure App Service has `WEBSITES_ENABLE_APP_SERVICE_STORAGE`=true or mount /home/site/wwwroot/data.

Twilio SMS:
 - Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, ADMIN_PHONE in env.

Blockchain (Phase 2):
 - Use `blockchain/DeviceRegistry.sol` and helper scripts.

If anything errors, copy/paste the terminal output here and I'll fix it immediately.
