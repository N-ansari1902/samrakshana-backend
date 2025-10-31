# Dockerfile - server
FROM python:3.11-slim

# ---- system deps (kept minimal) ----
RUN apt-get update && apt-get install -y --no-install-recommends gcc build-essential && rm -rf /var/lib/apt/lists/*

# set working dir Azure-friendly
WORKDIR /home/site/wwwroot

# create persistent data dir inside container path
RUN mkdir -p /home/site/wwwroot/data

COPY requirements.txt /home/site/wwwroot/requirements.txt
RUN pip install --no-cache-dir -r /home/site/wwwroot/requirements.txt

COPY . /home/site/wwwroot

EXPOSE 5000

# Use gunicorn in prod (server:app matches server.py)
CMD ["gunicorn", "-b", "0.0.0.0:5000", "server:app", "--workers", "2", "--threads", "4", "--timeout", "120"]
