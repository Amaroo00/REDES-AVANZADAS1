FROM python:3.10-slim


RUN apt-get update && apt-get install -y \
    iproute2 \
    iputils-ping \
    net-tools \
    telnet \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY App.py .


CMD ["/bin/bash"]
