#!/bin/bash

# Azure App Service startup script for Streamlit
# This script starts the Streamlit application on Azure

echo "Starting VDH Helpdesk App..."

# Install ODBC Driver 18 for SQL Server (if not already installed)
if [ ! -f /opt/microsoft/msodbcsql18/lib64/libmsodbcsql-18.3.so.2.1 ]; then
    echo "Installing ODBC Driver 18 for SQL Server..."
    curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
    curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
    apt-get update
    ACCEPT_EULA=Y apt-get install -y msodbcsql18
    apt-get install -y unixodbc-dev
fi

# Create .streamlit directory if it doesn't exist
mkdir -p ~/.streamlit

# Create Streamlit config file
cat > ~/.streamlit/config.toml << EOF
[server]
port = 8000
headless = true
address = "0.0.0.0"
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false
serverAddress = "vdh-helpdesk-app-dxh7cpcgh2e9gngt.eastus2-01.azurewebsites.net"
serverPort = 443

[client]
showErrorDetails = false
EOF

# Create secrets file from environment variables
cat > ~/.streamlit/secrets.toml << EOF
[connections.helpdesk]
server = "$SQL_SERVER"
database = "$SQL_DATABASE"
username = "$SQL_USERNAME"
password = "$SQL_PASSWORD"
driver = "ODBC Driver 18 for SQL Server"
EOF

echo "Configuration complete. Starting Streamlit..."

# Start Streamlit
python -m streamlit run helpdesk_app.py --server.port=8000 --server.address=0.0.0.0
