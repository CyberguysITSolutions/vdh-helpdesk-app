# Use Ubuntu 22.04 base so we can install msodbcsql18 reliably
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

# Install system packages and Python 3.11
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates apt-transport-https gnupg2 lsb-release build-essential \
    software-properties-common python3.11 python3.11-venv python3.11-dev python3-pip unixodbc-dev \
  && rm -rf /var/lib/apt/lists/*

# Add Microsoft package repo and install msodbcsql18 (ODBC driver for SQL Server)
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
  && curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list \
  && apt-get update \
  && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18 \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt early to leverage Docker cache
COPY requirements.txt /app/requirements.txt

# Create an isolated virtualenv and put it on PATH
RUN python3.11 -m venv /opt/venv
ENV PATH=" /opt/venv/bin:\

# Upgrade pip and install Python requirements into the venv (isolated from system packages)
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy application source
COPY . /app

# Expose the Streamlit port
EXPOSE 8000

# Start the Streamlit app using the venv python
CMD [\python\,\-m\,\streamlit\,\run\,\helpdesk_app.py\,\--server.port=8000\,\--server.address=0.0.0.0\,\--server.headless=true\]
