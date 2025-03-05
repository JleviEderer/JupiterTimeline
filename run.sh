
#!/bin/bash

# Display environment information
echo "Starting with user $(whoami)"
echo "Current directory: $(pwd)"

# Try different Python commands to find available Python
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    echo "Error: Python not found. Please install Python."
    exit 1
fi

echo "Using Python: $($PYTHON_CMD --version)"

# Check if required packages are installed
$PYTHON_CMD -c "import streamlit" 2>/dev/null || $PYTHON_CMD -m pip install -r requirements.txt

# Start health check server in background on port 8080
echo "Starting health check server on port 8080..."
$PYTHON_CMD health_check.py &
HEALTH_PID=$!

# Wait for health check server to start
sleep 2
echo "Health check server started with PID $HEALTH_PID"

# Start Streamlit server
echo "Starting Streamlit server..."
$PYTHON_CMD -m streamlit run app.py --server.address=0.0.0.0 --server.port=7860 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false --server.enableWebsocketCompression=false

# Cleanup health check server when Streamlit exits
echo "Cleaning up health check server"
kill $HEALTH_PID || echo "Failed to kill health check server"
